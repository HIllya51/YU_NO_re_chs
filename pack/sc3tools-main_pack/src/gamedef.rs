use crate::text::EncodingMaps;
use itertools::Itertools;
use nom::{
    bytes::complete::is_not,
    character::complete::{char, line_ending, not_line_ending},
    combinator::{map, map_opt, map_res, opt},
    multi::separated_list0,
    sequence::{delimited, pair, preceded, tuple},
    IResult,
};
use rust_embed::RustEmbed;
use std::{borrow::Cow, collections::HashMap, ops::RangeInclusive};

#[derive(RustEmbed)]
#[folder = "resources/"]
struct ResourceDir;

#[derive(Copy, Clone, Eq, PartialEq)]
pub enum Game {
    SteinsGateHD,
    SteinsGate0,
    RoboticsNotes,
    RoboticsNotesDash,
}

lazy_static! {
    pub static ref DEFS: Vec<GameDef> = vec![
        GameDef::new(
            Game::SteinsGateHD,
            "Steins;Gate Steam",
            "sghd",
            &["sghd", "steinsgatehd"],
            None,
            vec!['\'', '-', '[', ']', '(', ')']
        ),
        GameDef::new(
            Game::SteinsGate0,
            "Steins;Gate 0",
            "sg0",
            &["sg0", "steinsgate0"],
            Some('\u{E12F}'..='\u{E2AF}'),
            vec!['\'']
        ),
        GameDef::new(
            Game::RoboticsNotes,
            "Robotics;Notes",
            "rn",
            &["rn", "roboticsnotes"],
            None,
            vec!['\'', '-', '[', ']', '(', ')']
        ),
        GameDef::new(
            Game::RoboticsNotesDash,
            "Robotics;Notes DaSH",
            "rnd",
            &["rnd", "roboticsnotesdash"],
            None,
            vec!['\'']
        ),
        GameDef::new(
            Game::RoboticsNotesDash,
            "yuno",
            "yuno",
            &["yuno", "yuno"],
            None,
            vec![]
        ),
    ];
}

pub struct GameDef {
    #[allow(dead_code)]
    game: Game,
    pub full_name: &'static str,
    pub aliases: &'static [&'static str],
    #[allow(dead_code)]
    reserved_codepoints: Option<RangeInclusive<char>>,
    charset: Vec<char>,
    pub compound_chars: HashMap<char, String>,
    pub encoding_maps: EncodingMaps,
    pub fullwidth_blocklist: Vec<char>,
}

impl GameDef {
    pub fn new(
        game: Game,
        full_name: &'static str,
        resource_dir: &'static str,
        aliases: &'static [&'static str],
        reserved_codepoints: Option<RangeInclusive<char>>,
        fullwidth_blocklist: Vec<char>,
    ) -> Self {
        fn file_path(resource_dir: &'static str, name: &'static str) -> String {
            format!("{}/{}", resource_dir, name)
        }

        let charset: Cow<[u8]> =
            ResourceDir::get(&file_path(resource_dir, "charset.utf8")).unwrap();
        let charset: Vec<char> = std::str::from_utf8(charset.as_ref())
            .unwrap()
            .chars()
            .collect();
        let compound_chars: Cow<[u8]> =
            ResourceDir::get(&file_path(resource_dir, "compound_chars.map")).unwrap();
        let compound_chars = std::str::from_utf8(compound_chars.as_ref()).unwrap();
        let compound_chars = parse_compound_ch_map(compound_chars);
        let encoding_maps = EncodingMaps::new(&charset, &compound_chars);

        if let Err(err) = encoding_maps {
            panic!(
                "Error while constructing encoding maps for {}. \
                The following Private Use Area characters were not found in the charset: [{}]",
                full_name,
                err.missing_pua_chars
                    .into_iter()
                    .map(|ch| format!("'{}'", ch.escape_unicode()))
                    .join(", ")
            );
        }

        Self {
            game,
            full_name,
            aliases,
            reserved_codepoints,
            charset,
            compound_chars,
            encoding_maps: encoding_maps.unwrap(),
            fullwidth_blocklist,
        }
    }

    pub fn charset(&self) -> &[char] {
        &self.charset
    }
}

#[allow(dead_code)]
pub fn get(game: Game) -> &'static GameDef {
    DEFS.iter().find(|x| x.game == game).unwrap()
}

pub fn get_by_alias(alias: &str) -> Option<&'static GameDef> {
    DEFS.iter().find(|x| x.aliases.contains(&alias))
}

#[derive(Eq, PartialEq, Debug)]
struct PuaMapping<'a> {
    codepoint_range: RangeInclusive<char>,
    ch: &'a str,
}

impl<'a> PuaMapping<'a> {
    fn new(codepoint_range: RangeInclusive<char>, ch: &'a str) -> Self {
        Self {
            codepoint_range,
            ch,
        }
    }

    pub fn parse(i: &str) -> IResult<&str, PuaMapping> {
        fn codepoint(i: &str) -> IResult<&str, char> {
            map_opt(
                map_res(is_not("-]"), |s| u32::from_str_radix(s, 16)),
                std::char::from_u32,
            )(i)
        }

        fn range(i: &str) -> IResult<&str, RangeInclusive<char>> {
            map(
                delimited(
                    char('['),
                    pair(codepoint, opt(preceded(char('-'), codepoint))),
                    char(']'),
                ),
                |(a, b)| match (a, b) {
                    (a, Some(b)) => (a..=b),
                    _ => (a..=a),
                },
            )(i)
        }

        map(tuple((range, char('='), not_line_ending)), |(r, _, ch)| {
            PuaMapping::new(r, ch)
        })(i)
    }
}

fn parse_compound_ch_map(i: &str) -> HashMap<char, String> {
    let mappings = separated_list0(line_ending, PuaMapping::parse)(i).unwrap().1;
    mappings
        .iter()
        .flat_map(|m| {
            m.codepoint_range
                .clone()
                .map(move |codepoint| (codepoint, m.ch.to_string()))
        })
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parse_pua_mapping() {
        assert_eq!(
            PuaMapping::parse("[E01C]=meow").unwrap().1,
            PuaMapping::new('\u{E01C}'..='\u{E01C}', "meow")
        );

        assert_eq!(
            PuaMapping::parse("[E01C-E01F]=¹⁸").unwrap().1,
            PuaMapping::new('\u{E01C}'..='\u{E01F}', "¹⁸")
        );
    }
}
