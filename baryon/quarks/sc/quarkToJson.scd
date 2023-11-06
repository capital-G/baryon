q = ();

q[\quarkFile] = "QUARK_FILE".getenv;
q[\jsonFile] = "QUARK_JSON_FILE".getenv;

q[\toJson] = {|v|
	var val = case
	{v.class == Association} { q[\toJson].value(v.key) }
	{v===true} { "true" }
	{v===false} { "false" }
	{v.isString} { "\"%\"".format(v.replace("\"", "\\\"")).replace("\n", "\\n").replace("\t", " ") }
	{v.class == Symbol } { "\"%\"".format(v.asString.replace("\"", "\\\"")).replace("\n", "\\n") }
	{v.isNil} {val = "null"}
	{v.isFloat} { "%".format(v)}
	{v.isInteger} { "%".format(v)}
	{v.isArray} {
		var jsonRepArray = v.collect{|i| q[\toJson].value(i)};
		val = "%".format(jsonRepArray);
	}
	{v.isFunction} { "\"a function\"" }
	{v.class == Event} {
		var string = "{";
		v.pairsDo({|k, v|
			string = string + "\"%\": %,".format(k, q[\toJson].(v));
		});
		// remove last ,
		string = string[0..string.size-2];
		string = string + "}";
		string;
	}
	{ "\"%\"".format(v.replace("\"", "\\\"")).replace("\n", "\\n") };
	val;
};

"Extracting from % to %".format(q[\quarkFile], q[\jsonFile]).postln;


File(q[\jsonFile], "w").write(
    q[\toJson].value(thisProcess.interpreter.compileFile(q[\quarkFile]).value);
).close();

thisProcess.shutdown();

0.exit;
