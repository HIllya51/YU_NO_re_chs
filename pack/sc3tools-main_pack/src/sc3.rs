use byteorder::{BigEndian, WriteBytesExt};
use nom::{
    bytes::complete::{tag, take},
    combinator::{cond, map, peek, recognize, verify},
    multi::many_till,
    number::complete::{be_u16, be_u8},
    sequence::terminated,
    IResult,
};
use std::{borrow::Cow, fmt, io};

#[derive(Debug)]
pub enum Error {
    Io(io::Error),
    ExpectedMoreInput,
    UnrecognizedInstr(u8),
}

impl std::error::Error for Error {}

#[derive(Clone)]
pub struct Sc3String<'a>(pub Cow<'a, [u8]>);

impl<'a> Sc3String<'_> {
    pub fn iter(&self) -> Sc3StringIter {
        Sc3StringIter { remaining: &self.0 }
    }
}

pub struct Sc3StringIter<'a> {
    remaining: &'a [u8],
}

impl<'a> Iterator for Sc3StringIter<'a> {
    type Item = Result<StringToken<'a>, Error>;

    fn next(&mut self) -> Option<Self::Item> {
        if self.remaining.is_empty() {
            return None;
        }
        match StringToken::decode(&self.remaining) {
            Ok((rem, tk)) => {
                self.remaining = rem;
                if let StringToken::Terminator = tk {
                    None
                } else {
                    Some(Ok(tk))
                }
            }
            Err(err) => Some(Err(err)),
        }
    }
}

#[derive(Debug, Clone, Eq, PartialEq)]
pub enum StringToken<'a> {
    Text(Cow<'a, [u16]>),
    LineBreak,
    NameStart,
    LineStart,
    Present(PresentAction),
    Color(Expr<'a>),
    RubyBaseStart,
    RubyTextStart,
    RubyTextEnd,
    FontSize(u16),
    Parallel,
    Center,
    MarginTop(u16),
    MarginLeft(u16),
    HardcodedValue(u16),
    Eval(Expr<'a>),
    AutoForward,
    #[allow(non_camel_case_types)]
    AutoForward_1A,
    RubyCenterPerChar,
    AltLineBreak,
    Terminator,
}

#[derive(Debug, Clone, Eq, PartialEq)]
pub enum PresentAction {
    None,
    ResetAlignment,
    #[allow(non_camel_case_types)]
    Unknown_0x05,
    #[allow(non_camel_case_types)]
    Unknown_0x18,
}

#[derive(Debug, Clone, Eq, PartialEq)]
pub struct Expr<'a>(pub Cow<'a, [u8]>);

impl<'a> Expr<'a> {
    pub fn parse(i: &'a [u8]) -> IResult<&'a [u8], Self> {
        map(recognize(many_till(Self::token, tag(&[0x00u8]))), |slice| {
            Expr(Cow::from(slice))
        })(i)
    }

    fn token(i: &[u8]) -> IResult<&[u8], &[u8]> {
        let (i, b) = peek(be_u8)(i)?;
        if b >= 0x80u8 {
            terminated(Self::sc3_const, take(1usize))(i)
        } else {
            take(2usize)(i)
        }
    }

    fn sc3_const(i: &[u8]) -> IResult<&[u8], &[u8]> {
        let (i, peek) = peek(be_u8)(i)?;
        take(Self::const_len(peek))(i)
    }

    fn const_len(b: u8) -> usize {
        (((b & 0xE0) - 0x80) / 0x20 + 1) as usize
    }
}

impl<'a> StringToken<'_> {
    pub fn decode(i: &[u8]) -> Result<(&[u8], StringToken), Error> {
        fn parse<'a, O, P, F>(i: &'a [u8], parser: P, f: F) -> Result<(&[u8], StringToken), Error>
        where
            P: Fn(&'a [u8]) -> IResult<&'a [u8], O>,
            F: Fn(O) -> StringToken<'a>,
        {
            let (i, val) = parser(i).map_err(|_| Error::ExpectedMoreInput)?;
            Ok((i, f(val)))
        }

        fn peek_op(i: &[u8]) -> IResult<&[u8], u8> {
            let (_, b) = peek(be_u8)(i)?;
            let (i, _) = cond(b < 0x80u8 || b == 0xFFu8, take(1usize))(i)?;
            Ok((i, b))
        }

        fn text(i: &[u8]) -> IResult<&[u8], Vec<u16>> {
            let (i, (chars, _)) =
                many_till(be_u16, verify(peek(be_u8), |b| *b < 0x80u8 || *b == 0xFFu8))(i)?;
            Ok((i, chars))
        }

        let (i, op) = peek_op(i).map_err(|_| Error::ExpectedMoreInput)?;
        match op {
            0x00 => Ok((i, StringToken::LineBreak)),
            0x01 => Ok((i, StringToken::NameStart)),
            0x02 => Ok((i, StringToken::LineStart)),
            0x03 => Ok((i, StringToken::Present(PresentAction::None))),
            0x04 => parse(i, Expr::parse, StringToken::Color),
            0x05 => Ok((i, StringToken::Present(PresentAction::Unknown_0x05))),
            0x08 => Ok((i, StringToken::Present(PresentAction::ResetAlignment))),
            0x09 => Ok((i, StringToken::RubyBaseStart)),
            0x0A => Ok((i, StringToken::RubyTextStart)),
            0x0B => Ok((i, StringToken::RubyTextEnd)),
            0x0C => parse(i, be_u16, StringToken::FontSize),
            0x0E => Ok((i, StringToken::Parallel)),
            0x0F => Ok((i, StringToken::Center)),
            0x11 => parse(i, be_u16, StringToken::MarginTop),
            0x12 => parse(i, be_u16, StringToken::MarginLeft),
            0x13 => parse(i, be_u16, StringToken::HardcodedValue),
            0x15 => parse(i, Expr::parse, StringToken::Eval),
            0x18 => Ok((i, StringToken::Present(PresentAction::Unknown_0x18))),
            0x19 => Ok((i, StringToken::AutoForward)),
            0x1A => Ok((i, StringToken::AutoForward_1A)),
            0x1E => Ok((i, StringToken::RubyCenterPerChar)),
            0x1F => Ok((i, StringToken::AltLineBreak)),
            0xFF => Ok((i, StringToken::Terminator)),

            0x14 => Ok((i, StringToken::AutoForward)),
            0x1B => Ok((i, StringToken::AutoForward)),
            0x7 => Ok((i, StringToken::AutoForward)),
            #[allow(overlapping_patterns)]
            0x00..=0x7F => Err(Error::UnrecognizedInstr(op)),
            _ => parse(i, text, |chars| StringToken::Text(chars.into())),
        }
    }

    pub fn encode(&self, sink: &mut impl io::Write) -> Result<(), io::Error> {
        if let StringToken::Text(chars) = self {
            for code in chars.iter() {
                sink.write_u16::<BigEndian>(*code)?;
            }
            return Ok(());
        }

        let code: u8 = match self {
            StringToken::LineBreak => 0x00,
            StringToken::NameStart => 0x01,
            StringToken::LineStart => 0x02,
            StringToken::Present(PresentAction::None) => 0x03,
            StringToken::Color(_) => 0x04,
            StringToken::Present(PresentAction::Unknown_0x05) => 0x05,
            StringToken::Present(PresentAction::ResetAlignment) => 0x08,
            StringToken::RubyBaseStart => 0x09,
            StringToken::RubyTextStart => 0x0A,
            StringToken::RubyTextEnd => 0x0B,
            StringToken::FontSize(_) => 0x0C,
            StringToken::Parallel => 0x0E,
            StringToken::Center => 0x0F,
            StringToken::MarginTop(_) => 0x11,
            StringToken::MarginLeft(_) => 0x12,
            StringToken::HardcodedValue(_) => 0x13,
            StringToken::Eval(_) => 0x15,
            StringToken::Present(PresentAction::Unknown_0x18) => 0x18,
            StringToken::AutoForward => 0x19,
            StringToken::AutoForward_1A => 0x1A,
            StringToken::RubyCenterPerChar => 0x1E,
            StringToken::AltLineBreak => 0x1F,
            StringToken::Terminator => 0xFF,
            StringToken::Text(_) => unreachable!(),
        };

        sink.write(&code.to_be_bytes()).map(|_| ())?;

        match self {
            StringToken::Color(expr) => sink.write(&expr.0),
            StringToken::FontSize(val) => sink.write(&val.to_be_bytes()),
            StringToken::MarginTop(val) => sink.write(&val.to_be_bytes()),
            StringToken::MarginLeft(val) => sink.write(&val.to_be_bytes()),
            StringToken::Eval(expr) => sink.write(&expr.0),
            StringToken::HardcodedValue(val) => sink.write(&val.to_be_bytes()),
            _ => Ok(0usize),
        }
        .map(|_| ())
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
            Error::UnrecognizedInstr(op) => write!(f, "unrecognized instruction ({:#X})", op),
            Error::ExpectedMoreInput => write!(f, "expected more input"),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn unrecognized_instr() {
        let i = vec![0x05u8];
        let res = StringToken::decode(&i);
        println!("{:?}", res);
        assert_eq!(res.is_err(), true);
    }

    #[test]
    fn parse_expr() {
        let expr = vec![0x29, 0x0A, 0xA0, 0x5A, 0x14, 0x14, 0x00, 0x80, 0x00, 0x00];
        assert_eq!(Expr::parse(&expr).unwrap().1, Expr(Cow::from(&expr)));
    }
}
