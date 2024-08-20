# Py-SDelete-Filename-Finder
This program helps identify $J artifacts created during SDelete execution by analyzing the NTFS Change Journal.

![Demo](https://github.com/ksyeung/Py-SDelete-Filename-Finder/blob/main/Recording.gif?raw=true)

Malicious actors sometimes utilise [Sysinternals SDelete](https://learn.microsoft.com/en-us/sysinternals/downloads/sdelete) to wipe files they've dropped in order to prevent recovery and forensic analysis. As part of this wiping process, it rewrites the filename, which will look like "AAAA.AAA", "BBBB.BBB", "CCCC.CCC", ... , "ZZZZ.ZZZ". This leaves a distinct pattern in $J, the USN Journal. If you suspect SDelete may have been used because you've found evidence of execution, this tool may be useful to you.

How does it work?

1) It searches $J for this filename rewriting pattern, which has the same timestamp corresponding to these operations: 'DataOverwrite', 'RenameNewName', 'RenameOldName', and 'FileDelete|Close'.
2) Once it has found records with these operations, it filters by the MFT Entry Number (also known as a File Reference Number) to ensure its looking at the entries that map to the same file, and notes the original filename just prior to deletion.
4) It lets you know all of the original filenames it has found (and, if you've opted for it, it will have written the results to a CSV file).

How do you use it?
- You'll need Joakim Schicht's [ExtractUsnJrnl](https://github.com/jschicht/ExtractUsnJrnl) to grab the change journal.
  `ExtractUsnJrnl.exe /DevicePath:c: /OutputName:J.bin`
- You'll need Eric Zimmerman's [MFTECmd](https://github.com/EricZimmerman/MFTECmd) to parse the change journal (Note: --fl is used in this case to compel full precision timestamps, which is not otherwise provided).
  `MFTECmd.exe -f J.bin --csv . --fl`
- Now that you've got a CSV export of $J, you'll pass it through to sdelete_filename_finder.py.
`python sdelete_filename_finder.py --f  .\J.csv --o .\sdeleted_filenames.csv`

Usage notes:
- The '-o' arg is optional.
