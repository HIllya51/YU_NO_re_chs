use crate::gamedef;
use crate::sc3;
use crate::text;

use gamedef::GameDef;
use nom::{
    branch::alt,
    bytes::complete::{is_not, tag, take, take_while, take_while1, take_while_m_n},
    character::complete::{char, space1},
    combinator::{map, map_res, opt, peek, recognize, rest, verify},
    multi::{many1, many_till},
    sequence::{delimited, preceded, tuple},
    IResult,
};
use sc3::{Sc3String, StringToken};
use std::fmt::Write;
use std::{borrow::Cow, error, fmt, io::Cursor};

#[derive(Debug)]
pub enum Error {
    Parsing(ParseError),
    TextEncoding(text::EncodingError),
    Serialization(sc3::Error),
}

#[derive(Debug, Eq, PartialEq)]
pub enum ParseError {
    MissingAttribute(String),
    UnexpectedAttribute(String),
    IllegalAttributeValue((String, String)),
}

impl error::Error for Error {}
impl error::Error for ParseError {}

#[derive(Debug, Eq, PartialEq)]
pub struct CozString<'a>(pub Cow<'a, str>);

pub struct CozStringIter<'a> {
    remaining: &'a str,
}

#[derive(Debug, Clone, Eq, PartialEq)]
pub enum StringSegment<'a> {
    Text(text::Text<'a>),
    Tag(Tag<'a>),
}

type Attr<'a> = (&'a str, Cow<'a, str>);

#[derive(Eq, PartialEq, Debug, Clone)]
pub struct Tag<'a> {
    name: &'a str,
    attr: Option<Attr<'a>>,
}

impl fmt::Display for StringSegment<'_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            StringSegment::Text(s) => write!(f, "{}", s.as_str()),
            StringSegment::Tag(tag) => {
                if let Some(ref attr) = tag.attr {
                    write!(f, "[{} {}=\"{}\"]", tag.name, attr.0, attr.1)
                } else {
                    write!(f, "[{}]", tag.name)
                }
            }
        }
    }
}

impl fmt::Display for CozString<'_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", &self.0)
    }
}

impl<'a> Sc3String<'_> {
    pub fn serialize(
        &self,
        gamedef: &GameDef,
        keep_fullwidth_chars: bool,
    ) -> Result<CozString, Error> {
        let mut buf = String::new();
        for tk in self.iter() {
            let seg = tk?.serialize(&gamedef, keep_fullwidth_chars)?;
            write!(buf, "{}", seg).unwrap();
        }

        Ok(CozString(Cow::from(buf)))
    }

    pub fn deserialize(
        s: &'a CozString,
        gamedef: &GameDef,
        convert_to_fullwidth: bool,
    ) -> Result<Sc3String<'a>, Error> {
        let mut buf = Cursor::new(Vec::new());
        for seg in s.iter() {
            let tk = StringToken::deserialize(&seg, &gamedef, convert_to_fullwidth)?;
            tk.encode(&mut buf).unwrap();
        }

        StringToken::Terminator.encode(&mut buf).unwrap();
        Ok(Sc3String(buf.into_inner().into()))
    }
}

impl<'a> CozString<'a> {
    pub fn iter(&self) -> CozStringIter {
        CozStringIter { remaining: &self.0 }
    }
}

impl<'a> Iterator for CozStringIter<'a> {
    type Item = StringSegment<'a>;

    fn next(&mut self) -> Option<Self::Item> {
        if self.remaining.is_empty() {
            None
        } else {
            let (rem, seg) = StringSegment::parse(&self.remaining);
            self.remaining = rem;
            Some(seg)
        }
    }
}

impl<'a> Tag<'a> {
    pub fn new(name: &'a str, attr: Option<Attr<'a>>) -> Self {
        Self { name, attr }
    }

    pub fn is_known_tag(s: &'a str) -> bool {
        Self::parse(&s)
            .ok()
            .map(|(_, tag)| tag.is_known())
            .unwrap_or_default()
    }

    pub fn is_known(&self) -> bool {
        matches!(StringToken::from_tag(&self), Ok(Some(_)) | Err(_))
    }

    pub fn parse(input: &'a str) -> IResult<&str, Self> {
        delimited(
            char('['),
            map(
                tuple((is_not(" ]"), opt(preceded(space1, Self::attr)))),
                |(name, val)| Tag::new(name, val.map(|(k, v)| (k, Cow::from(v)))),
            ),
            char(']'),
        )(input)
    }

    fn attr(input: &str) -> IResult<&str, (&str, &str)> {
        fn string_literal(input: &str) -> IResult<&str, &str> {
            delimited(tag("\""), is_not("\""), tag("\""))(input)
        }

        tuple((
            take_while1(|c| c != '='),
            preceded(tag("="), string_literal),
        ))(input)
    }
}

impl<'a> StringSegment<'a> {
    pub fn parse(input: &'a str) -> (&str, Self) {
        alt((
            map(Self::tag, |tag| StringSegment::Tag(tag)),
            map(Self::text, |s| {
                StringSegment::Text(text::Text(Cow::from(s)))
            }),
        ))(input)
        .expect("StringSegment::parse() should never fail.")
    }

    fn tag(i: &str) -> IResult<&str, Tag> {
        verify(Tag::parse, Tag::is_known)(i)
    }

    fn text(i: &str) -> IResult<&str, &str> {
        recognize(many_till(
            take(1usize),
            verify(peek(rest), |s: &str| Tag::is_known_tag(s) || s.is_empty()),
        ))(i)
    }
}

impl<'a> StringToken<'a> {
    pub fn serialize(
        self,
        gamedef: &GameDef,
        keep_fullwidth_chars: bool,
    ) -> Result<StringSegment, text::EncodingError> {
        if let StringToken::Text(encoded_text) = self {
            let s = text::decode_str(&encoded_text, &gamedef, keep_fullwidth_chars)?;
            return Ok(StringSegment::Text(s.into()));
        }

        let (name, attr) = match self {
            StringToken::LineBreak => ("linebreak", None),
            StringToken::NameStart => ("name", None),
            StringToken::LineStart => ("line", None),
            StringToken::Present(action) => (
                match action {
                    sc3::PresentAction::None => "%p",
                    sc3::PresentAction::ResetAlignment => "%e",
                    sc3::PresentAction::Unknown_0x05 => "%05",
                    sc3::PresentAction::Unknown_0x18 => "%18",
                },
                None,
            ),
            StringToken::RubyBaseStart => ("ruby-base", None),
            StringToken::RubyTextStart => ("ruby-text-start", None),
            StringToken::RubyTextEnd => ("ruby-text-end", None),
            StringToken::RubyCenterPerChar => ("ruby-center-per-char", None),
            StringToken::Parallel => ("parallel", None),
            StringToken::Center => ("center", None),
            StringToken::MarginLeft(val) => ("margin", Some(("left", val.to_string()))),
            StringToken::MarginTop(val) => ("margin", Some(("top", val.to_string()))),
            StringToken::Terminator => ("", None),
            StringToken::Color(expr) => ("color", Some(("index", hex::encode_upper(&expr.0)))),
            StringToken::FontSize(val) => ("font", Some(("size", val.to_string()))),
            StringToken::HardcodedValue(val) => {
                ("hardcoded-value", Some(("index", val.to_string())))
            }
            StringToken::Eval(expr) => ("evaluate", Some(("expr", hex::encode_upper(&expr.0)))),
            StringToken::AutoForward => ("auto-forward", None),
            StringToken::AutoForward_1A => ("auto-forward-1a", None),
            StringToken::AltLineBreak => ("alt-linebreak", None),
            StringToken::Text(_) => unreachable!(),
        };
        Ok(StringSegment::Tag(Tag::new(
            name,
            attr.map(|(k, v)| (k, v.into())),
        )))
    }

    pub fn deserialize(
        seg: &'a StringSegment,
        gamedef: &GameDef,
        convert_to_fullwidth: bool,
    ) -> Result<Self, Error> {
        match seg {
            StringSegment::Text(s) => text::encode_str(s, gamedef, convert_to_fullwidth)
                .map(|x| StringToken::Text(x.into()))
                .map_err(Into::into),
            StringSegment::Tag(tag) => Self::from_tag(&tag).map(Option::unwrap).map_err(Into::into),
        }
    }

    pub fn from_tag<'t: 'a>(tag: &Tag<'t>) -> Result<Option<Self>, ParseError> {
        let res = match tag.name {
            "linebreak" => Ok(StringToken::LineBreak),
            "alt-linebreak" => Ok(StringToken::AltLineBreak),
            "name" => Ok(StringToken::NameStart),
            "line" => Ok(StringToken::LineStart),
            "%p" => Ok(StringToken::Present(sc3::PresentAction::None)),
            "%e" => Ok(StringToken::Present(sc3::PresentAction::ResetAlignment)),
            "%05" => Ok(StringToken::Present(sc3::PresentAction::Unknown_0x05)),
            "%18" => Ok(StringToken::Present(sc3::PresentAction::Unknown_0x18)),
            "color" => Self::expr_attr(tag.attr.as_ref(), "index").map(StringToken::Color),
            "ruby-base" | "rubybase" => Ok(StringToken::RubyBaseStart),
            "ruby-text-start" | "rubytextstart" => Ok(StringToken::RubyTextStart),
            "ruby-text-end" | "rubytextend" => Ok(StringToken::RubyTextEnd),
            "ruby-center-per-char" => Ok(StringToken::RubyCenterPerChar),
            "parallel" => Ok(StringToken::Parallel),
            "center" => Ok(StringToken::Center),
            "margin" => match tag.attr.as_ref().map(|x| x.0) {
                Some("left") => {
                    Self::u16_attr(tag.attr.as_ref(), "left").map(StringToken::MarginLeft)
                }
                Some("top") => Self::u16_attr(tag.attr.as_ref(), "top").map(StringToken::MarginTop),
                Some(name) => Err(ParseError::UnexpectedAttribute(name.to_string())),
                None => Err(ParseError::MissingAttribute("left | top".to_string())),
            },
            "font" => match tag.attr.as_ref().map(|x| x.0) {
                Some("size") => {
                    Self::u16_attr(tag.attr.as_ref(), "size").map(StringToken::FontSize)
                }
                Some(name) => Err(ParseError::UnexpectedAttribute(name.to_string())),
                None => Err(ParseError::MissingAttribute("size".to_string())),
            },
            "hardcoded-value" | "hardcodedvalue" => {
                Self::u16_attr(tag.attr.as_ref(), "index").map(StringToken::HardcodedValue)
            }
            "auto-forward" | "autoforward" => Ok(StringToken::AutoForward),
            "auto-forward-1a" => Ok(StringToken::AutoForward_1A),
            "evaluate" => Self::expr_attr(tag.attr.as_ref(), "expr").map(StringToken::Eval),
            _ => return Ok(None),
        };
        res.map(|x| Some(x))
    }

    fn get_attr<'val, T: 'val>(
        attr: Option<&Attr<'a>>,
        expected_name: &'a str,
        parser: impl FnOnce(&str) -> IResult<&str, T>,
    ) -> Result<T, ParseError> {
        let attr = match attr {
            Some((name, _)) if *name == expected_name => Ok(attr.unwrap()),
            Some((name, _)) => Err(ParseError::UnexpectedAttribute(name.to_string())),
            _ => Err(ParseError::MissingAttribute(expected_name.to_string())),
        }?;
        let (_, e) = parser(&attr.1).map_err(|_| {
            ParseError::IllegalAttributeValue((attr.0.to_string(), attr.1.to_string()))
        })?;
        Ok(e)
    }

    fn u16_attr(attr: Option<&Attr<'a>>, name: &'a str) -> Result<u16, ParseError> {
        fn u16_literal(value: &str) -> IResult<&str, u16> {
            map_res(take_while(|c: char| c.is_digit(10)), |s| {
                u16::from_str_radix(s, 10)
            })(value)
        }

        Self::get_attr(attr, name, u16_literal)
    }

    fn expr_attr<'expr>(
        attr: Option<&Attr<'a>>,
        name: &'a str,
    ) -> Result<sc3::Expr<'expr>, ParseError> {
        fn expr<'expr>(i: &str) -> IResult<&str, sc3::Expr<'expr>> {
            map(hex_string, |vec| sc3::Expr(vec.into()))(i)
        }

        fn hex_string(value: &str) -> IResult<&str, Vec<u8>> {
            many1(map_res(
                take_while_m_n(2, 2, |c: char| c.is_digit(16)),
                |hex| u8::from_str_radix(hex, 16),
            ))(value)
        }

        Self::get_attr(attr, name, expr)
    }
}

impl From<ParseError> for Error {
    fn from(err: ParseError) -> Self {
        Error::Parsing(err)
    }
}

impl From<text::EncodingError> for Error {
    fn from(err: text::EncodingError) -> Self {
        Error::TextEncoding(err)
    }
}

impl From<sc3::Error> for Error {
    fn from(err: sc3::Error) -> Self {
        Error::Serialization(err)
    }
}

impl fmt::Display for ParseError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            ParseError::MissingAttribute(attr) => write!(f, "missing attribute: '{}'", attr),
            ParseError::UnexpectedAttribute(attr) => write!(f, "unexpected attribute: '{}'", attr),
            ParseError::IllegalAttributeValue(attr) => {
                write!(f, "illegal value '{}' for attribute '{}'", attr.1, attr.0)
            }
        }
    }
}

impl fmt::Display for Error {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Error::Parsing(err) => fmt::Display::fmt(&err, f),
            Error::TextEncoding(err) => fmt::Display::fmt(&err, f),
            Error::Serialization(err) => fmt::Display::fmt(&err, f),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn token_serialization_roundtrip() {
        let gamedef = gamedef::get(gamedef::Game::SteinsGate0);
        let text = StringSegment::parse("sample text").1;
        assert_eq!(
            StringToken::deserialize(&text, &gamedef, false)
                .map(|tk| tk.serialize(&gamedef, false).unwrap())
                .unwrap(),
            text
        );

        let text = StringSegment::parse("[meow]").1;
        assert_eq!(
            StringToken::deserialize(&text, &gamedef, false)
                .map(|tk| tk.serialize(&gamedef, false).unwrap())
                .unwrap(),
            text
        );
    }

    #[test]
    fn serialization_roundtrip() -> Result<(), Box<dyn error::Error>> {
        let gamedef = gamedef::get(gamedef::Game::SteinsGate0);
        let src = CozString(Cow::from("[name]LuLu[line]Hi I am LuLu"));
        let sc3 = Sc3String::deserialize(&src, &gamedef, false)?;
        assert_eq!(src, sc3.serialize(&gamedef, false)?);
        Ok(())
    }

    #[test]
    fn test_parse_errors() {
        test_error("[evaluate expr=\"meow\"]", |res| {
            if let Err(Error::Parsing(ParseError::IllegalAttributeValue((k, v)))) = res {
                (k, v) == ("expr".to_string(), "meow".to_string())
            } else {
                false
            }
        });
        test_error("[color]", |res| {
            if let Err(Error::Parsing(ParseError::MissingAttribute(name))) = res {
                name == "index".to_string()
            } else {
                false
            }
        });
        test_error("[margin cat=\"LuLu\"]", |res| {
            if let Err(Error::Parsing(ParseError::UnexpectedAttribute(name))) = res {
                name == "cat".to_string()
            } else {
                false
            }
        });
    }

    fn test_error(text: &str, f: impl FnOnce(Result<StringToken, Error>) -> bool) {
        let gamedef = gamedef::get(gamedef::Game::SteinsGate0);
        let seg = StringSegment::parse(&text).1;
        let res = StringToken::deserialize(&seg, &gamedef, false);
        assert!(f(res));
    }

    #[test]
    fn parse_attr() {
        assert_eq!(Tag::attr("key=\"value\""), Ok(("", ("key", "value"))));
    }

    #[test]
    fn parse_tag() {
        assert_eq!(Tag::parse("[meow]"), Ok(("", Tag::new("meow", None))));

        assert_eq!(
            Tag::parse("[cat sound=\"meow\"]"),
            Ok(("", Tag::new("cat", Some(("sound", "meow".into())))))
        );

        assert_eq!(
            Tag::parse("[cat     sound=\"meow\"]"),
            Ok(("", Tag::new("cat", Some(("sound", "meow".into())))))
        );
    }

    #[test]
    fn parse_text_segment() {
        assert_eq!(
            StringSegment::parse("Sample Text[margin top=\"38\"]"),
            (
                "[margin top=\"38\"]",
                StringSegment::Text(text::Text(Cow::from("Sample Text")))
            )
        );

        assert_eq!(
            StringSegment::parse("Sample Text[margin]"),
            (
                "[margin]",
                StringSegment::Text(text::Text(Cow::from("Sample Text")))
            )
        );

        assert_eq!(
            StringSegment::parse("Sample Text[meow]"),
            (
                "",
                StringSegment::Text(text::Text(Cow::from("Sample Text[meow]")))
            )
        );
    }

    #[test]
    fn parse_tag_segment() {
        assert_eq!(
            StringSegment::parse("[color index=\"ABCD\"]"),
            (
                "",
                StringSegment::Tag(Tag::new("color", Some(("index", Cow::from("ABCD")))))
            )
        );
    }
}
