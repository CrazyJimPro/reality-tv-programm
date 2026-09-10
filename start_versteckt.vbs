' Startet start_versteckt.bat ohne sichtbares Konsolenfenster (Fensterstil 0).
' Wird von der Desktop-Verknuepfung als Ziel verwendet - siehe start.bat,
' Schritt "Desktop-Verknuepfung anlegen".
'
' WScript.Shell.Run fuehrt .bat-Dateien nicht zuverlaessig direkt aus (die
' Windows-Dateizuordnung fuer .bat greift hier nicht immer) - deshalb wird
' explizit ueber cmd.exe /c aufgerufen. Ein einzelnes Anfuehrungszeichen-Paar
' um den Pfad reicht (cmd.exe entfernt es korrekt, auch bei Leerzeichen im
' Pfad) - der doppelte Anfuehrungszeichen-Kniff ist nur noetig, wenn dem
' Pfad noch weitere Argumente folgen, was hier nicht der Fall ist.
Dim objShell, objFSO, scriptDir, anfuehrungszeichen, batPfad, befehl

Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")
scriptDir = objFSO.GetParentFolderName(WScript.ScriptFullName)
anfuehrungszeichen = Chr(34)
batPfad = scriptDir & "\start_versteckt.bat"
befehl = "cmd.exe /c " & anfuehrungszeichen & batPfad & anfuehrungszeichen

objShell.Run befehl, 0, False
