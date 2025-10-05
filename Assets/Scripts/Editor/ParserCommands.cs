using System;
using System.IO;
using Import;
using UnityEditor;

namespace Editor
{
    public class ParserCommands
    {
        [MenuItem("PhysFun/ParseNormalStructure")]
        public static void ParseNormalStructure()
        {
            var files = Directory.GetFiles(Environment.GetFolderPath(Environment.SpecialFolder.Desktop));
            foreach (var file in files)
            {
                var fileInfo = new FileInfo(file);
                if(fileInfo.Extension.Equals(".json"))
                    JsonToTpsheetParser.Parse(file, false);
            }
        }
    }
}