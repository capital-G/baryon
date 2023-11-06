q = ();

q[\renderHelp] = {|helpSourcePath, helpTargetPath|
	var helpSourceFiles;

	if(helpTargetPath.notNil, {
		SCDoc.helpTargetDir = helpTargetPath;
	});

	// find help source files
	helpSourceFiles = [];
	PathName(helpSourcePath).filesDo({|filePath|
		// filePath is of class PathName
		if(filePath.extension == "schelp", {
			helpSourceFiles = helpSourceFiles.add(
				// helpSoureFiles needs to be relative
				filePath.asRelativePath(helpSourcePath),
			);
		});
	});

	"Found % help files".format(helpSourceFiles.size).postln;

	// render help source files
	helpSourceFiles.do({|helpSourceFile|
		var doc;

		"Render %/%".format(helpSourcePath, helpSourceFile).postln;
		doc = SCDoc.parseFileMetaData(helpSourcePath, helpSourceFile);

		if(doc.notNil, {
			SCDoc.parseAndRender(doc);
		}, {
			"Error on parisng % - will skip".format(helpSourceFile);
		});
	});
};

"Building docs".postln;

/*
q[\renderHelp].value(
	helpSourcePath: "/Users/scheiba/github/sc-quarks/baryon/repos/AllGui", // "QUARK_HELP_SOURCE_PATH".getenv;
	helpTargetPath: "/Users/scheiba/github/sc-quarks/baryon/sc_docs", //"QUARK_HELP_TARGET_PATH".getenv;
);
*/

q[\renderHelp].value(
	helpSourcePath: "QUARK_HELP_SOURCE_PATH".getenv,
	helpTargetPath: "QUARK_HELP_TARGET_PATH".getenv,
);

thisProcess.shutdown();

0.exit;
