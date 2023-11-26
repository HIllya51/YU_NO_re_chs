use std::{
    cell::RefCell, collections::HashMap, error, fmt, fs::File, io, io::BufReader, io::BufWriter,
    marker::PhantomData, ops::Range,
};

use crate::sc3;
use byteorder::{LittleEndian, WriteBytesExt};
use io::{Read, Seek, SeekFrom, Write};
use nom::{
    bytes::complete::tag, combinator::map, multi::many0, number::complete::le_u32,
    sequence::preceded, sequence::tuple, IResult,
};
use sc3::Sc3String;

#[derive(Debug)]
pub enum Error {
    UnrecognizedFormat,
    CorruptedFile,
    Io(io::Error),
}

impl error::Error for Error {}

pub fn open(mut file: File) -> Result<Box<dyn MagesScript>, Error> {
    let mut magic = [0; 4];
    file.read_exact(&mut magic)?;
    file.seek(SeekFrom::Start(0))?;
    let magic = std::str::from_utf8(&magic).map_err(|_| Error::UnrecognizedFormat)?;

    if magic == Scx::magic() {
        Ok(Box::new(Script::<Scx>::open(file)?))
    } else if magic == Msb::magic() {
        Ok(Box::new(Script::<Msb>::open(file)?))
    } else if magic == Scx2::magic() {
        Ok(Box::new(Script::<Scx2>::open(file)?))
    } else {
        Err(Error::UnrecognizedFormat)
    }
}

pub trait MagesScript {
    fn string_index(&self) -> &StringIndex;
    fn read_string<'a>(&self, handle: StringHandle) -> io::Result<Sc3String<'a>>;
    fn replace_strings<'a>(&mut self, changes: &HashMap<usize, Sc3String<'a>>) -> io::Result<()>;
}

pub struct Script<F: Format> {
    reader: RefCell<BufReader<File>>,
    writer: BufWriter<File>,
    pub string_index: StringIndex,
    pub string_index_location: Range<u32>,
    phantom: PhantomData<F>,
}

pub trait Format {
    fn magic() -> &'static str;
    fn str_index_location(header: &[u8]) -> IResult<&[u8], Range<u32>>;
    fn str_index(i: &[u8]) -> IResult<&[u8], Vec<StringIndexEntry>>;
    fn str_seek_origin() -> StrSeekOrigin;
    fn write_offset(offset: u32, writer: &mut (impl Seek + Write)) -> io::Result<()>;
}

pub enum StrSeekOrigin {
    FileStart,
    HeapStart,
}

pub struct StringHandle(pub Range<u32>);

impl StringHandle {
    pub fn size(&self) -> usize {
        self.0.len()
    }
}
pub struct StringIndex {
    entries: Vec<StringIndexEntry>,
    seek_from: u32,
    eof: u32,
}

#[derive(Debug, Copy, Clone)]
pub struct StringIndexEntry {
    pub id: u32,
    pub offset: u32,
}

impl StringIndexEntry {
    pub fn new(id: u32, offset: u32) -> Self {
        Self { id, offset }
    }
}

pub struct StringIndexIter<'a> {
    index: &'a StringIndex,
    pos: usize,
}

impl<F: Format> Script<F> {
    pub fn open(file: File) -> Result<Self, Error> {
        let mut reader = BufReader::new(file.try_clone()?);
        let mut header = [0; 16];
        reader.read_exact(&mut header)?;
        let (_, str_index_loc) =
            F::str_index_location(&header).map_err(|_| Error::UnrecognizedFormat)?;

        reader.seek(SeekFrom::Start(str_index_loc.start as u64))?;
        let mut buf = vec![0u8; str_index_loc.len()];
        reader.read_exact(&mut buf)?;
        let (_, str_index_entries) = F::str_index(&buf).map_err(|_| Error::CorruptedFile)?;
        let seek_from = match F::str_seek_origin() {
            StrSeekOrigin::FileStart => 0,
            StrSeekOrigin::HeapStart => str_index_loc.end,
        };
        let eof = reader.seek(SeekFrom::End(0))?;

        let writer = BufWriter::new(file.try_clone()?);

        Ok(Self {
            reader: RefCell::new(reader),
            writer,
            string_index_location: str_index_loc,
            string_index: StringIndex::new(str_index_entries, seek_from, eof as u32),
            phantom: PhantomData,
        })
    }
}

impl<F: Format> MagesScript for Script<F> {
    fn string_index(&self) -> &StringIndex {
        &self.string_index
    }

    fn read_string<'a>(&self, handle: StringHandle) -> io::Result<Sc3String<'a>> {
        let mut reader = self.reader.borrow_mut();
        reader.seek(SeekFrom::Start(handle.0.start.into()))?;
        let mut buf = vec![0u8; handle.size()];
        reader.read_exact(&mut buf)?;
        Ok(Sc3String(buf.into()))
    }

    fn replace_strings<'a>(&mut self, changes: &HashMap<usize, Sc3String<'a>>) -> io::Result<()> {
        if self.string_index.entries.is_empty() {
            return Ok(());
        }
        let lines = self
            .string_index
            .iter()
            .enumerate()
            .map(|(i, handle)| {
                changes
                    .get(&i)
                    .map(|s| Ok(s.clone()))
                    .unwrap_or_else(|| self.read_string(handle))
            })
            .collect::<Result<Vec<_>, _>>()?;

        let heap_start = self.string_index.entries[0].offset;
        let base_offset = match F::str_seek_origin() {
            StrSeekOrigin::FileStart => heap_start,
            StrSeekOrigin::HeapStart => 0,
        };

        let offsets = lines.iter().scan(base_offset, |acc, x| {
            let offset = Some(*acc);
            *acc += x.0.len() as u32;
            offset
        });

        let mut writer = &mut self.writer;
        writer.seek(SeekFrom::Start(heap_start as u64))?;
        for s in &lines {
            writer.write(&s.0)?;
        }

        writer.seek(SeekFrom::Start(self.string_index_location.start as u64))?;
        for offset in offsets {
            F::write_offset(offset, &mut writer)?;
        }

        Ok(())
    }
}

impl StringIndex {
    pub fn new(entries: Vec<StringIndexEntry>, seek_from: u32, eof: u32) -> Self {
        Self {
            entries,
            seek_from,
            eof,
        }
    }

    pub fn count(&self) -> usize {
        self.entries.len()
    }

    pub fn iter(&self) -> StringIndexIter {
        StringIndexIter {
            index: &self,
            pos: 0,
        }
    }

    pub fn get(&self, index: usize) -> Option<StringHandle> {
        if index < self.entries.len() {
            let range = if index < self.entries.len() - 1 {
                self.entries[index].offset + self.seek_from
                    ..self.entries[index + 1].offset + self.seek_from
            } else {
                self.entries[index].offset + self.seek_from..self.eof
            };
            Some(StringHandle(range))
        } else {
            None
        }
    }
}

impl Iterator for StringIndexIter<'_> {
    type Item = StringHandle;

    fn next(&mut self) -> Option<Self::Item> {
        let next = self.index.get(self.pos);
        if next.is_some() {
            self.pos += 1;
        }
        next
    }
}

pub struct Scx {}

impl Format for Scx {
    fn magic() -> &'static str {
        "SC3\0"
    }

    fn str_index_location(header: &[u8]) -> IResult<&[u8], Range<u32>> {
        map(
            preceded(tag("SC3\0"), tuple((le_u32, le_u32))),
            |(start, end)| start..end,
        )(header)
    }

    fn str_index(i: &[u8]) -> IResult<&[u8], Vec<StringIndexEntry>> {
        many0(map(le_u32, |offset| StringIndexEntry::new(0, offset)))(i)
    }

    fn str_seek_origin() -> StrSeekOrigin {
        StrSeekOrigin::FileStart
    }

    fn write_offset(offset: u32, writer: &mut (impl Seek + Write)) -> io::Result<()> {
        writer.write_u32::<LittleEndian>(offset)
    }
}

pub struct Scx2 {}

impl Format for Scx2 {
    fn magic() -> &'static str {
        "\x3d\x01\x33\x00"
    }

    fn str_index_location(header: &[u8]) -> IResult<&[u8], Range<u32>> {
        map(
            preceded(tag("\x3d\x01\x33\x00"), tuple((le_u32, le_u32))),
            |(start, end)| start..end,
        )(header)
    }

    fn str_index(i: &[u8]) -> IResult<&[u8], Vec<StringIndexEntry>> {
        many0(map(le_u32, |offset| StringIndexEntry::new(0, offset)))(i)
    }

    fn str_seek_origin() -> StrSeekOrigin {
        StrSeekOrigin::FileStart
    }

    fn write_offset(offset: u32, writer: &mut (impl Seek + Write)) -> io::Result<()> {
        writer.write_u32::<LittleEndian>(offset)
    }
}
pub struct Msb {}

impl Format for Msb {
    fn magic() -> &'static str {
        "MES\0"
    }

    fn str_index_location(header: &[u8]) -> IResult<&[u8], Range<u32>> {
        map(
            preceded(tag("MES\0"), tuple((le_u32, le_u32, le_u32))),
            |(_, _, end)| 16..end,
        )(header)
    }

    fn str_index(i: &[u8]) -> IResult<&[u8], Vec<StringIndexEntry>> {
        many0(map(tuple((le_u32, le_u32)), |(id, offset)| {
            StringIndexEntry::new(id, offset)
        }))(i)
    }

    fn str_seek_origin() -> StrSeekOrigin {
        StrSeekOrigin::HeapStart
    }

    fn write_offset(offset: u32, writer: &mut (impl Seek + Write)) -> io::Result<()> {
        writer.seek(SeekFrom::Current(4))?;
        writer.write_u32::<LittleEndian>(offset)
    }
}

impl From<io::Error> for Error {
    fn from(error: io::Error) -> Error {
        Error::Io(error)
    }
}

impl fmt::Display for Error {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Error::Io(err) => fmt::Display::fmt(&err, f),
            Error::UnrecognizedFormat => write!(f, "unrecognized format"),
            Error::CorruptedFile => write!(f, "corrupted file"),
        }
    }
}
