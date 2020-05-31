
![Python package build status](https://img.shields.io/github/workflow/status/wonkyweirdy/stramp/Python%20package)

# stramp

Timestamp a structured text document such that the content of any section or subsection can later be proved
to have existed at (approximately) the time the document was stamped.

**STR**uctured text st**AMP** &rarr; STRAMP

This tool uses
[decentralized trusted timestamping](https://en.wikipedia.org/wiki/Trusted_timestamping#Decentralized_timestamping_on_the_blockchain)
technology that is backed by the Bitcoin [blockchain](https://en.wikipedia.org/wiki/Blockchain_(database)).
The protocol used is [OpenTimestamps](https://opentimestamps.org/). Servers supporting this protocol are public
and free to use.

The advantage of Stramp over using another [OpenTimestamps client](https://pypi.org/project/opentimestamps-client/)
directly is that you can prove one or more chosen sections of your document selectively without revealing
the content of the entire document. This is useful if you collect notes for a project in a large file where
some sections may have information you don't want to reveal and other sections have text for which you might
want timestamp proof at some later time.

It is intended for this command to be run periodically in the background with a service such as
[cron](https://en.wikipedia.org/wiki/Cron). I'd recommend setting it up to run once or twice a day.

## Applications

This tool has the same applications as digital trusted timestamping in general, but the convenience and zero cost
make it much more practical. Set it up to run in the background on your note files, and with practically
no further effort you'll get the benefit in case you ever need it: 

- Patent documentation - This can't be directly used to win a patent since everyone has switched to first-to-file.
However, it may still be useful for [defensive publication](https://en.wikipedia.org/wiki/Defensive_publication)
to prevent someone else from patenting an idea you came up with.

- Trade secrets - Prove that you had the idea of doing something a certain way.

- Simple bragging rights - Write your idea or prediction in your notes so you can later prove you had it
at a specific date. 

## Installation

Stramp requires Python 3.6 or newer. In addition to the Python library dependencies (automatically installed,
assuming you use `pip`), you will also need the `ots` command from
[opentimestamps-client](https://pypi.org/project/opentimestamps-client/):

```
pip install opentimestamps-client
```

If Stramp is available from [PyPI](https://pypi.org/project/stramp/), you can install it with:

```
pip install stramp
```

Other options are to install it from the GitHub repository directly:

```
pip install -U 'git+https://github.com/wonkyweirdy/stramp#egg=stramp'
```

or to install from a cloned git repository:

```
git clone https://github.com/wonkyweirdy/stramp.git
pip install ./stramp
```

## How it works

1. Each document files is copied to create an archive copy. The archive copy is stored in the directory
`~/.stramp/data` named based on the hash of the file.

2. The text of each document, individual sections, and recursive subsections, is hashed using a
[secure hash algorithm](https://en.wikipedia.org/wiki/Secure_Hash_Algorithms) to produce
hexadecimal hash strings. These hash strings are collected into a JSON file along with the associated file paths
and some other metadata. The JSON file goes in the `~/.stramp/new` directory.

4. The generated JSON hash file is then timestamped using the `ots stamp` command. Once stamped, the JSON hash file
and its associated `*.ots` file are moved into the `~/.stramp/stamped` directory. At this point, the stamp data will
have been submitted to the public calendar servers. It will take time for the timestamp to be processed on the
servers.

5. The stamp file (`*.ots`) is upgraded using `ots upgrade`. Once upgraded, the JSON hash file
and its associated `*.ots` file are moved into the `~/.stramp/complete` directory. The upgraded stamp will
contain all the information needed to trace the timestamp back to the specific transaction and block in the
Bitcoin blockchain. Note that for a hash file stamped on the current run, the upgrade will happen on a subsequent
run. It can take a few hours before the path is confirmed into a Bitcoin block. There is a built-in age limit
that will prevent new (less than eight hours old) stamps from being upgraded; this is to help ensure that all the
servers had enough time to process the stamp completely.

The `new` and `stamped` directories are used as queues. If the `ots stamp` or `ots upgade` command fails for a
hash file on one run, it will be retried on a later run.

## Stamp verification

Stramp does not implement anything to help with verification. The easiest way to check a stamp is to drop it
onto the [opentimestamps.org](https://opentimestamps.org/) web page. If you want to check it locally, it is more
involved since you need to run (or have access to) a server running Bitcoin Core.

## Configuration

The configuration file is expected to be at `~/.stramp/config.json`.

Example content:

```json
{
    "ots_command_path": "/usr/local/bin/ots",
    "documents": [
        "/home/joe/Documents/personal-notes.org",
        "/home/joe/Documents/project1/project1.org"
    ]
}
```

The `ots_command_path` specification is optional. It defaults to just `"ots"`, expecting that command to be found
in the command search path.

## Document formats

### Org-mode

Currently, only [Org-mode](https://orgmode.org/) format as UTF-8 is supported since this is what I use for my notes.
The Org-mode support may not even be complete since have only implemented it to support the Org features
I use.

### Future formats

I would consider adding support for other
[lightweight markup languages](https://en.wikipedia.org/wiki/Lightweight_markup_language):

- [Markdown](https://en.wikipedia.org/wiki/Markdown) (flavors?)
- [reStructuredText](https://docutils.sourceforge.io/rst.html)
- [MediaWiki Wikitext](https://www.mediawiki.org/wiki/Wikitext)
- [Tiki Wiki](https://doc.tiki.org/Wiki-Syntax-Text)
- [DokuWiki](https://www.dokuwiki.org/wiki:syntax)
- others?

Maybe other structured document formats:

- HTML
- ENEX (Evernote)

## Legal

My *opinion* is that this tool should *in principal* allow creating indisputable proof that the text of a
section of a document existed at a specific point of time. The proof will continue to be indisputable for
as long as the cryptography involved can be trusted. However, we don't know for sure there isn't someone in a
secret lab somewhere able to trivially forge an SHA-2 hash.

I can't promise this tool is appropriate for any certain use case. Users need to evaluate this for themselves.
Quoth the LICENSE file:

> The software is provided "as is", without warranty of any kind, express or implied, including but not limited to the
> warranties of merchantability, fitness for a particular purpose and non-infringement. In no event shall the authors or
> copyright holders be liable for any claim, damages or other liability, whether in an action of contract, tort or
> otherwise, arising from, out of or in connection with the software or the use or other dealings in the software.

## Similar and related projects

- https://opentimestamps.org/
- https://github.com/opentimestamps/opentimestamps-client
- https://github.com/reale/timestampy
- https://github.com/bitpay/i-made-this
