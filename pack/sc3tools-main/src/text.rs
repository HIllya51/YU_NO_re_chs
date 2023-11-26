use nom::{
    branch::alt, bytes::complete::is_not, character::complete::anychar, character::complete::char,
    combinator::map, combinator::map_res, combinator::recognize, sequence::delimited, IResult,
};

use crate::gamedef::GameDef;
use std::{borrow::Cow, collections::HashMap, error, fmt};

pub const FULLWIDTH_SPACE: char = '\u{3000}';

#[derive(Debug, Eq, PartialEq, Clone)]
pub struct Text<'a>(pub Cow<'a, str>);

#[derive(Eq, PartialEq, Debug, Clone)]
pub enum Char<'a> {
    Regular(char),
    Compound(&'a str),
}

impl<'a> Text<'a> {
    pub fn iter(&self, encoding_maps: &'a EncodingMaps) -> CharIterator {
        CharIterator {
            remaining: &self.0,
            encoding_maps,
        }
    }

    pub fn as_str(&self) -> &str {
        &self.0
    }

    pub fn from_chars(
        chars: impl Iterator<Item = Char<'a>>,
        keep_fullwidth_chars: bool,
    ) -> Text<'a> {
        let mut buf = String::new();
        for res in chars {
            match res {
                Char::Regular(mut c) => {
                    if !keep_fullwidth_chars {
                        c = replace_fullwidth(c);
                    }

                    buf.push(c);
                }
                Char::Compound(s) => {
                    buf.push('[');
                    buf.push_str(&s);
                    buf.push(']');
                }
            }
        }

        Text(buf.into())
    }
}

pub struct CharIterator<'a> {
    remaining: &'a str,
    encoding_maps: &'a EncodingMaps,
}

impl<'a> Iterator for CharIterator<'a> {
    type Item = Char<'a>;

    fn next(&mut self) -> Option<Self::Item> {
        fn next_char<'a>(s: &'a str, encoding_maps: &EncodingMaps) -> IResult<&'a str, Char<'a>> {
            let encode_compound = move |ch| encode_compound_char(ch, &encoding_maps);
            let compound = delimited(
                char('['),
                recognize(map_res(is_not("]"), encode_compound)),
                char(']'),
            );

            alt((map(compound, Char::Compound), map(anychar, Char::Regular)))(s)
        }

        let res = next_char(&self.remaining, &self.encoding_maps).ok();
        if let Some((rem, ch)) = res {
            self.remaining = rem;
            Some(ch)
        } else {
            None
        }
    }
}

#[derive(Debug, Eq, PartialEq)]
pub enum EncodingError {
    IllegalCharCode(u16),
    CharNotInCharset(String),
    PuaCharNotMapped(u16, char),
}

impl error::Error for EncodingError {}

#[derive(Debug)]
pub struct EncodingMapConstructionError {
    pub missing_pua_chars: Vec<char>,
}

pub struct EncodingMaps {
    main: HashMap<char, u16>,
    compound: HashMap<String, u16>,
}

impl EncodingMaps {
    pub fn new(
        charset: &[char],
        pua_mappings: &HashMap<char, String>,
    ) -> Result<Self, EncodingMapConstructionError> {
        let main: HashMap<_, _> = (0..charset.len())
            .map(|i| {
                let high_byte = 0x80u8 + (i / 256) as u8;
                let low_byte = (i % 256) as u8;
                let code = (high_byte as u16) << 8u16 | (low_byte as u16);
                (charset[i], code)
            })
            .collect();

        let lookup_compound = |ch| main.get(ch).ok_or_else(|| *ch);

        let (compound, missing): (Vec<_>, Vec<_>) = pua_mappings
            .iter()
            .map(|(k, v)| lookup_compound(k).map(|code| (v.clone(), *code)))
            .partition(Result::is_ok);

        if !missing.is_empty() {
            return Err(EncodingMapConstructionError {
                missing_pua_chars: missing.into_iter().map(Result::unwrap_err).collect(),
            });
        }

        let compound: HashMap<_, _> = compound.into_iter().map(Result::unwrap).collect();
        Ok(EncodingMaps { main, compound })
    }
}

pub fn encode_str(
    s: &Text,
    gamedef: &GameDef,
    convert_to_fullwidth: bool,
) -> Result<Vec<u16>, EncodingError> {
    let mut buf = Vec::new();
    for mut ch in s.iter(&gamedef.encoding_maps) {
        if let Char::Regular(c) = &ch {
            if convert_to_fullwidth && !gamedef.fullwidth_blocklist.contains(&*c) {
                ch = Char::Regular(replace_halfwidth(*c));
            } else if *c == '\u{20}' {
                ch = Char::Regular(FULLWIDTH_SPACE);
            }
        }
        buf.push(encode_char(&ch, &gamedef)?);
    }

    Ok(buf)
}

fn encode_char(ch: &Char, gamedef: &GameDef) -> Result<u16, EncodingError> {
    match ch {
        Char::Compound(s) => encode_compound_char(s, &gamedef.encoding_maps),
        Char::Regular(c) => encode_regular_char(*c, &gamedef.encoding_maps),
    }
}

fn encode_regular_char(c: char, encoding_maps: &EncodingMaps) -> Result<u16, EncodingError> {
    encoding_maps
        .main
        .get(&c)
        .cloned()
        .ok_or_else(|| EncodingError::CharNotInCharset(c.to_string()))
}

fn encode_compound_char(ch: &str, encoding_maps: &EncodingMaps) -> Result<u16, EncodingError> {
    encoding_maps
        .compound
        .get(ch)
        .cloned()
        .ok_or_else(|| EncodingError::CharNotInCharset(ch.to_string()))
}

pub fn decode_str<'a>(
    s: &[u16],
    gamedef: &'a GameDef,
    keep_fullwidth_chars: bool,
) -> Result<Text<'a>, EncodingError> {
    let chars = s
        .iter()
        .map(|code| decode_char(*code, gamedef.charset(), &gamedef.compound_chars))
        .collect::<Result<Vec<_>, _>>()?;
    Ok(Text::from_chars(chars.into_iter(), keep_fullwidth_chars))
}

pub fn decode_char<'a>(
    code: u16,
    charset: &[char],
    compound_map: &'a HashMap<char, String>,
) -> Result<Char<'a>, EncodingError> {
    let i = (code & 0x7FFF) as usize;
    let ch = charset
        .get(i)
        .cloned()
        .ok_or_else(|| EncodingError::IllegalCharCode(code))?;
    if let '\u{e000}'..='\u{f8ff}' = ch {
        // Private Use Area
        compound_map
            .get(&ch)
            .map(|s| Char::Compound(s))
            .ok_or_else(|| EncodingError::PuaCharNotMapped(code, ch))
    } else {
        Ok(Char::Regular(ch))
    }
}

pub fn to_halfwidth<'a>(s: &'a Text, encoding_maps: &'a EncodingMaps) -> Text<'a> {
    Text::from_chars(s.iter(encoding_maps), false)
}

pub fn is_fullwidth_ch(ch: char) -> bool {
    ('\u{ff00}'..='\u{ff7f}').contains(&ch)
}

fn replace_halfwidth(ch: char) -> char {
    match ch {
        '\u{20}' => FULLWIDTH_SPACE,
        '\u{21}'..='\u{007f}' => std::char::from_u32(ch as u32 + 0xfee0u32).unwrap(),
        _ => ch,
    }
}

pub fn replace_fullwidth(ch: char) -> char {
    match ch {
        '\u{ff00}'..='\u{ff7f}' => std::char::from_u32(ch as u32 - 0xfee0u32).unwrap(),
        FULLWIDTH_SPACE => '\u{20}',
        _ => ch,
    }
}

impl fmt::Display for EncodingError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            EncodingError::IllegalCharCode(code) => {
                write!(f, "illegal character code ({:#X})", code)
            }
            EncodingError::CharNotInCharset(ch) => {
                write!(f, "character '{}' is not present in the charset", ch)
            }
            EncodingError::PuaCharNotMapped(code, ch) => write!(
                f,
                "{:#X} corresponds to a private use area character '{}' which isn't properly mapped.",
                code,
                ch.escape_unicode()
            ),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::gamedef;

    #[test]
    fn char_iter_regular() {
        let gamedef = gamedef::get(gamedef::Game::SteinsGate0);
        let text = Text(Cow::from("A"));
        let ch = text.iter(&gamedef.encoding_maps).next().unwrap();
        assert_eq!(ch, Char::Regular('A'));
    }

    #[test]
    fn char_iter_compound() {
        let gamedef = gamedef::get(gamedef::Game::SteinsGate0);
        let text = Text(Cow::from("[ü]"));
        let ch = text.iter(&gamedef.encoding_maps).next().unwrap();
        assert_eq!(ch, Char::Compound("ü"));
    }

    #[test]
    fn encode_roundtrip_regular() {
        let gamedef = gamedef::get(gamedef::Game::SteinsGate0);
        let ch = Char::Regular('A');
        let code = encode_char(&ch, &gamedef).unwrap();
        let decoded = decode_char(code, gamedef.charset(), &gamedef.compound_chars);
        assert_eq!(decoded, Ok(ch));
    }

    #[test]
    fn encode_roundtrip_compound() {
        let gamedef = gamedef::get(gamedef::Game::SteinsGate0);
        let ch = Char::Compound("ü");
        let code = encode_char(&ch, &gamedef).unwrap();
        let decoded = decode_char(code, gamedef.charset(), &gamedef.compound_chars);
        assert_eq!(decoded, Ok(ch));
    }

    #[test]
    fn decode_invalid() {
        let gamedef = gamedef::get(gamedef::Game::SteinsGate0);
        let code = 40270u16;
        assert!(decode_char(code, gamedef.charset(), &gamedef.compound_chars).is_err());
    }
}
