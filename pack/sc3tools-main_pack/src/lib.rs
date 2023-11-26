#[macro_use]
extern crate lazy_static;
extern crate byteorder;
extern crate clap;
extern crate glob;
extern crate nom;
extern crate rust_embed;
extern crate termcolor;

mod coz;
mod format;
mod gamedef;
mod sc3;
mod text;

use clap::{App, AppSettings, Arg, SubCommand};
use core::fmt;
use coz::CozString;
use gamedef::GameDef;
use glob::Paths;
use itertools::{EitherOrBoth, Itertools};
use sc3::Sc3String;
use std::{
    collections::HashMap,
    error,
    fs::{self, OpenOptions},
    io,
    io::{BufRead, BufReader, BufWriter, Write},
    path::PathBuf,
};
use std::{error::Error, fs::File, path::Path};
use termcolor::{Color, ColorChoice, ColorSpec, StandardStream, WriteColor};

#[derive(Debug)]
enum ProcessingError {
    Script(PathBuf, usize, Box<dyn Error>),
    Text(PathBuf, usize, Box<dyn Error>),
    Io(io::Error),
    LineCountMismatch,
}

impl error::Error for ProcessingError {}

lazy_static! {
    static ref SUPPORTED_GAMES: String = {
        let aliases: Vec<_> = gamedef::DEFS.iter().map(|x| x.aliases.join("|")).collect();
        aliases.join(",")
    };
}

pub fn run() -> Result<(), Box<dyn Error>> {
    fn validate_game(alias: String) -> Result<(), String> {
        gamedef::get_by_alias(&alias)
            .map(|_| ())
            .ok_or_else(|| format!("try one of the following - {}", *SUPPORTED_GAMES))
    }

    fn parse_glob(arg: &str, pattern: &str) -> Result<Paths, String> {
        glob::glob(pattern).map_err(|err| format!("Invalid value for '<{}>'\n{}", arg, err))
    }

    fn game_arg(idx: u64) -> Arg<'static, 'static> {
        Arg::with_name("game")
            .help(&SUPPORTED_GAMES)
            .index(idx)
            .required(true)
            .validator(validate_game)
    }

    let after_help: String = {
        let games = gamedef::DEFS
            .iter()
            .map(|x| format!("{} ({})", x.full_name, x.aliases.join("|")))
            .collect::<Vec<_>>()
            .join("\n    ");
        "SUPPORTED GAMES:\n    ".to_owned() + &games
    };

    let matches = App::new("sc3tools")
        .setting(AppSettings::SubcommandRequiredElseHelp)
        .setting(AppSettings::DisableVersion)
        .author("Committee of Zero")
        .version("2.1")
        .after_help(&*after_help)
        .subcommand(
            SubCommand::with_name("extract-text")
                .about("Extracts text from one or multiple script files")
                .display_order(1)
                .setting(AppSettings::DisableVersion)
                .args(&[
                    Arg::with_name("input")
                        .help("Path to the input file or a glob pattern")
                        .index(1)
                        .required(true),
                    game_arg(2),
                    Arg::with_name("preserve-fullwidth")
                        .long("preserve-fullwidth")
                        .help("Preserve fullwidth characters"),
                ]),
        )
        .subcommand(
            SubCommand::with_name("replace-text")
                .about("Replaces the contents of one or multiple script files")
                .display_order(2)
                .setting(AppSettings::DisableVersion)
                .args(&[
                    Arg::with_name("scripts")
                        .help("Path to the input script file or a glob pattern")
                        .index(1)
                        .required(true),
                    Arg::with_name("text-files")
                        .help("Path to the input text file or a glob pattern")
                        .index(2)
                        .required(true),
                    game_arg(3),
                ]),
        )
        .get_matches();

    match matches.subcommand() {
        ("extract-text", Some(matches)) => {
            let input = matches.value_of("input").unwrap();
            let game = matches.value_of("game").unwrap();
            let gamedef = gamedef::get_by_alias(game).unwrap();
            let keep_fullwidth_chars = matches.is_present("preserve-fullwidth");
            run_extract_text(parse_glob("input", input)?, gamedef, keep_fullwidth_chars)
        }
        ("replace-text", Some(matches)) => {
            let scripts = matches.value_of("scripts").unwrap();
            let txts = matches.value_of("text-files").unwrap();
            let game = matches.value_of("game").unwrap();
            let gamedef = gamedef::get_by_alias(game).unwrap();

            run_replace_text(
                parse_glob("scripts", scripts)?,
                parse_glob("text-files", txts)?,
                &gamedef,
            )
        }
        _ => Ok(()),
    }
}

fn run_extract_text(
    paths: Paths,
    gamedef: &GameDef,
    keep_fullwidth_chars: bool,
) -> Result<(), Box<dyn Error>> {
    Ok(for entry in paths {
        let path = entry?;
        let out_dir = if let Some(script_dir) = path.parent() {
            let out_dir = script_dir.join("txt");
            fs::create_dir_all(&out_dir)?;
            out_dir
        } else {
            continue;
        };

        let stem = if let Some(stem) = path.file_stem().and_then(|s| s.to_str()) {
            stem.to_owned()
        } else {
            continue;
        };

        
        let ext = ".".to_owned() + &path.extension().unwrap_or_default().to_str().unwrap() + ".txt";
        let output = out_dir.join(stem + &ext);
        if let Err(err) = extract_text(&path, &output, gamedef, keep_fullwidth_chars) {
            println!("Processing {:?}...", path);
            report_err(err)
        }
    })
}

fn run_replace_text(
    scripts: Paths,
    text_files: Paths,
    game: &GameDef,
) -> Result<(), Box<dyn Error>> {
    let text_files: Vec<_> = text_files.map(|x| x.unwrap()).collect();
    Ok(for res in scripts {
        let script_path = res?;
        println!("Processing {:?}", script_path);
        let script_fname = script_path.file_name();
        let script_stem = script_path.file_stem();
        let txt_path = text_files.iter().find(|p| {
            let stem = p.file_stem();
            stem == script_stem || stem == script_fname
        });
        if let Some(txt_path) = txt_path {
            if let Err(err) = replace_text(script_path, txt_path, &game) {
                report_err(err)
            }
        }
    })
}

fn extract_text(
    script_path: &impl AsRef<Path>,
    out: &impl AsRef<Path>,
    gamedef: &GameDef,
    keep_fullwidth_chars: bool,
) -> Result<(), Box<dyn Error>> {
    let script = format::open(File::open(script_path)?)?;
    let txt = File::create(out)?;
    let mut writer = BufWriter::new(txt);

    let table = &script.string_index();
    for (i, handle) in table.iter().enumerate() {
        let line = script.read_string(handle)?;
        let serialized = line
            .serialize(&gamedef, keep_fullwidth_chars)
            .map_err(|err| {
                ProcessingError::Script(script_path.as_ref().to_owned(), i, Box::new(err))
            })?;
        writeln!(writer, "{}", serialized)?;
    }

    if table.count() > 0 {
        //report_ok(&format!("Sucessfully extracted {} lines.", table.count()));
    } else {
        //report_ok("No text data to be extracted.");
    }
    Ok(())
}

fn replace_text(
    script_file: impl AsRef<Path>,
    text_file: impl AsRef<Path>,
    gamedef: &GameDef,
) -> Result<(), Box<dyn Error>> {
    let file = OpenOptions::new()
        .read(true)
        .write(true)
        .open(&script_file)?;
    let mut script = format::open(file)?;
    let txt = BufReader::new(File::open(&text_file)?);

    let lines = script
        .string_index()
        .iter()
        .map(|x| script.read_string(x))
        .zip_longest(txt.lines().map(|res| res.map(|s| CozString(s.into()))));

    let mut changes = Vec::new();

    let scr_err = |err: Box<dyn Error>, line| {
        ProcessingError::Script(script_file.as_ref().to_owned(), line, err)
    };

    let txt_err =
        |err: Box<dyn Error>, line| ProcessingError::Text(text_file.as_ref().to_owned(), line, err);

    for (i, line_pair) in lines.enumerate() {
        if let EitherOrBoth::Both(scr_line, txt_line) = line_pair {
            let scr_line = scr_line?;
            let txt_line = txt_line?;
            for pair in scr_line.iter().zip_longest(txt_line.iter()) {
                match pair {
                    EitherOrBoth::Both(sc3, coz) => {
                        let eq = equivalent(&sc3?, &coz, &gamedef)
                            .map_err(|err| scr_err(Box::new(err), i))?;
                        if !eq {
                            changes.push((i, txt_line));
                            break;
                        }
                    }
                    EitherOrBoth::Left(sc3) => {
                        let _ = sc3?;
                        changes.push((i, txt_line));
                        break;
                    }
                    EitherOrBoth::Right(coz) => {
                        let _ = sc3::StringToken::deserialize(&coz, &gamedef, false)
                            .map_err(|err| txt_err(Box::new(err), i))?;
                        changes.push((i, txt_line));
                        break;
                    }
                };
            }
        } else {
            return Err(Box::new(ProcessingError::LineCountMismatch));
        }
    }

    let process_change = |i, s| {
        let index = &script.string_index();
        let orig = script.read_string(index.get(i).unwrap())?;
        let mut fullwidth = false;
        for tk in orig.iter() {
            let tk = tk.map_err(|err| scr_err(Box::new(err), i))?;
            if let sc3::StringToken::Text(text) = tk {
                let decoded = text::decode_str(&text, gamedef, true)
                    .map_err(|err| txt_err(Box::new(err), i))?;

                fullwidth = decoded.iter(&gamedef.encoding_maps).any(|ch| {
                    if let text::Char::Regular(c) = ch {
                        c != text::FULLWIDTH_SPACE
                            && text::is_fullwidth_ch(c)
                            && text::replace_fullwidth(c).is_ascii_alphanumeric()
                    } else {
                        false
                    }
                });

                if fullwidth {
                    break;
                }
            }
        }

        Sc3String::deserialize(s, &gamedef, fullwidth).map_err(|err| txt_err(Box::new(err), i))
    };

    let changes = changes
        .iter()
        .map(|(i, s)| Ok((*i, process_change(*i, s)?)))
        .collect::<Result<HashMap<_, _>, ProcessingError>>()?;

    script.replace_strings(&changes)?;

    if !changes.is_empty() {
        report_ok(&format!(
            "Successfully replaced {} out of {} lines.",
            changes.len(),
            script.string_index().count()
        ));
    } else {
        report_ok("No changes found.");
    }
    Ok(())
}

fn equivalent(
    scr_tk: &sc3::StringToken,
    txt_seg: &coz::StringSegment,
    gamedef: &GameDef,
) -> Result<bool, text::EncodingError> {
    if let coz::StringSegment::Text(txt_str) = txt_seg {
        if let sc3::StringToken::Text(scr_str) = scr_tk {
            let txt_str = text::to_halfwidth(&txt_str, &gamedef.encoding_maps);
            let scr_str = text::decode_str(&scr_str, &gamedef, false)?;
            return Ok(txt_str == scr_str);
        }
    }

    Ok(
        if let Ok(txt_tk) = sc3::StringToken::deserialize(txt_seg, &gamedef, false) {
            *scr_tk == txt_tk
        } else {
            false
        },
    )
}

fn report(message: &str) {
    let mut stderr = StandardStream::stderr(ColorChoice::Always);
    stderr
        .set_color(ColorSpec::new().set_fg(Some(Color::Red)))
        .unwrap();
    writeln!(&mut stderr, "{}\n", message).unwrap();
    stderr.set_color(&ColorSpec::default()).unwrap();
}

fn report_err(err: Box<dyn Error>) {
    let message = format!("Error: {}.", err);
    report(&message);
}

fn report_ok(message: &str) {
    let mut stdout = StandardStream::stdout(ColorChoice::Always);
    stdout
        .set_color(ColorSpec::new().set_fg(Some(Color::Green)))
        .unwrap();
    writeln!(&mut stdout, "{}\n", message).unwrap();
    stdout.set_color(&ColorSpec::default()).unwrap();
}

impl fmt::Display for ProcessingError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            ProcessingError::Script(path, line, err) => write!(
                f,
                "{}, line {}: {}",
                path.file_name().unwrap().to_string_lossy(),
                line + 1,
                err
            ),
            ProcessingError::Text(path, line, err) => write!(
                f,
                "{}, line {}: {}",
                path.file_name().unwrap().to_string_lossy(),
                line + 1,
                err
            ),
            ProcessingError::Io(err) => fmt::Display::fmt(err, f),
            ProcessingError::LineCountMismatch => write!(
                f,
                "The number of lines in the text file has to match that of the script file"
            ),
        }
    }
}

impl From<io::Error> for ProcessingError {
    fn from(err: io::Error) -> Self {
        ProcessingError::Io(err)
    }
}
