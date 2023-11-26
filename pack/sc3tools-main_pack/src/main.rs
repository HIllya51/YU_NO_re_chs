use std::process;

fn main() {
    if let Err(err) = sc3tools::run() {
        eprintln!("{}", err);
        process::exit(1);
    }
}
