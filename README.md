# Py-SDelete-Filename-Finder
This program helps identify $J artifacts created during SDelete execution by analyzing the NTFS Change Journal.

![Demo](https://github.com/ksyeung/Py-SDelete-Filename-Finder/blob/main/Recording.gif?raw=true)

Malicious actors sometimes utilise [Sysinternals SDelete](https://learn.microsoft.com/en-us/sysinternals/downloads/sdelete) to wipe files they've dropped in order to prevent recovery and forensic analysis. As part of this wiping process, it rewrites the filename, which will look like "AAAAAAAA.AAA", "BBBBBBBB.BBB", ... , "ZZZZZZZZ.ZZZ". This leaves a distinct pattern in $J, the Change Journal (also known as the USN Journal). If you've found evidence of SDelete execution, this tool may be useful to you.

How does it work?

1. It searches $J for this filename rewriting pattern, which has the same timestamp corresponding to these operations: 'DataOverwrite', 'RenameNewName', 'RenameOldName', and 'FileDelete|Close'
2. Once it has found records with these operations, it filters by the MFT Entry Number (also known as a File Reference Number) to ensure its looking at the entries that map to the same file, and notes the original filename just prior to deletion.
3. It lets you know all of the original filenames it has found (and, if you've opted for it, it will have written the results to a CSV file).

How do you use it?
- You'll need Joakim Schicht's [ExtractUsnJrnl](https://github.com/jschicht/ExtractUsnJrnl) to grab the change journal.


  `ExtractUsnJrnl.exe /DevicePath:c: /OutputName:J.bin`
- You'll need Eric Zimmerman's [MFTECmd](https://github.com/EricZimmerman/MFTECmd) to parse the change journal (Note: --fl is used in this case to compel full precision timestamps, which is not otherwise provided).


  `MFTECmd.exe -f J.bin --csv . --csvf J.csv --fl`
- Now that you've got a CSV export of $J, you'll pass it through to sdelete_filename_finder.py.


  `python sdelete_filename_finder.py --f  .\J.csv --o .\sdeleted_filenames.csv`


- Given the original filename, you may now want to correlate this evidence by checking Prefetch files.


How do you get the original file?
- There's a few places where you might find the original file.


1. Check the Volume Shadow Copy Service.
2. Check the Windows pagefile, as it may have been paged out to disk. The odds of this being the case go down if the registry value "ClearPageFileAtShutdown” is set to 1 at "HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management" and the system has already restarted (this is a Group Policy setting, “Shutdown: Clear virtual memory pagefile”).
3. You might find it in the hibernation file.
4. You might find it in unallocated disk space (even if the SDelete "-z" argument was used to zero out free space). Data remnants may persist if the device uses a physical SSD on Windows, due to SSD-specific behaviors like TRIM and wear-leveling.


Usage notes:
- The '-o' arg is optional.


References:
https://learn.microsoft.com/en-us/sysinternals/downloads/sdelete
https://github.com/jschicht/ExtractUsnJrnl
https://github.com/EricZimmerman/MFTECmd
https://attack.mitre.org/techniques/T1070/004
https://learn.microsoft.com/en-us/windows/win32/api/winioctl/ns-winioctl-usn_record_v2
