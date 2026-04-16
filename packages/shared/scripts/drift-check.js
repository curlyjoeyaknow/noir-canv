#!/usr/bin/env node

/**
 * Schema drift checker for Noir Canvas.
 *
 * Reads JSON Schema files from packages/shared/schemas/ and compares
 * field names against the Zod schemas (TypeScript) and Pydantic models
 * (Python) to detect drift between representations.
 *
 * Exit codes:
 *   0 — all three representations are in sync
 *   1 — drift detected (details printed to stderr)
 */

const fs = require("fs");
const path = require("path");

const SCHEMAS_DIR = path.resolve(__dirname, "..", "schemas");
const ZOD_FILE = path.resolve(__dirname, "..", "..", "..", "apps", "web", "lib", "schemas.ts");
const PYDANTIC_FILE = path.resolve(
  __dirname, "..", "..", "..", "pipeline", "src", "pipeline", "lib", "schemas.py"
);

let driftFound = false;

function reportDrift(schema, message) {
  console.error("  [DRIFT] " + schema + ": " + message);
  driftFound = true;
}

function extractJsonSchemaFields(schemaPath) {
  var raw = fs.readFileSync(schemaPath, "utf-8");
  var schema = JSON.parse(raw);
  var props = schema.properties || {};
  var required = schema.required || [];
  var requiredSet = {};
  required.forEach(function (r) { requiredSet[r] = true; });

  var fields = {};
  Object.keys(props).forEach(function (name) {
    fields[name] = { required: !!requiredSet[name] };
  });
  return fields;
}

function extractZodFields(source, schemaVarName) {
  var varName = schemaVarName + "Schema";
  var prefix1 = "export const " + varName + " = z.object({";
  var prefix2 = "export const " + varName + " = z.strictObject({";
  var startIdx = source.indexOf(prefix1);
  var usedPrefix = "export const " + varName + " = z.object(";
  if (startIdx === -1) {
    startIdx = source.indexOf(prefix2);
    usedPrefix = "export const " + varName + " = z.strictObject(";
  }
  if (startIdx === -1) return null;

  var braceStart = source.indexOf("{", startIdx + usedPrefix.length);
  var depth = 1;
  var i = braceStart + 1;
  while (i < source.length && depth > 0) {
    if (source[i] === "{") depth++;
    else if (source[i] === "}") depth--;
    i++;
  }
  var objectBody = source.substring(braceStart + 1, i - 1);

  var fields = {};
  var bodyLines = objectBody.split("\n");
  var braceDepth = 0;

  bodyLines.forEach(function (line) {
    var trimmed = line.trim();
    if (!trimmed || trimmed.indexOf("//") === 0) return;

    for (var c = 0; c < trimmed.length; c++) {
      if (trimmed[c] === "{" || trimmed[c] === "(") braceDepth++;
      else if (trimmed[c] === "}" || trimmed[c] === ")") braceDepth--;
    }

    if (braceDepth <= 0) {
      var m = trimmed.match(/^(\w+)\s*:/);
      if (m) {
        var fieldName = m[1];
        var isOpt = trimmed.indexOf(".optional()") !== -1;
        fields[fieldName] = { required: !isOpt };
      }
      braceDepth = 0;
    }
  });

  return fields;
}

function extractPydanticFields(source, className) {
  var marker = "class " + className + "(BaseModel):";
  var classIdx = source.indexOf(marker);
  if (classIdx === -1) return null;

  var bodyStart = classIdx + marker.length;

  // Find end: next "class " at start of line or "# ---" at start of line
  var bodyEnd = source.length;
  var remaining = source.substring(bodyStart);
  var lines = remaining.split("\n");
  var charCount = 0;

  for (var li = 1; li < lines.length; li++) {
    charCount += lines[li - 1].length + 1;
    var ltrim = lines[li].trimStart();
    if (ltrim.indexOf("class ") === 0 || ltrim.indexOf("# ---") === 0) {
      bodyEnd = bodyStart + charCount;
      break;
    }
  }

  var body = source.substring(bodyStart, bodyEnd);
  var bodyLines = body.split("\n");
  var fields = {};

  bodyLines.forEach(function (line) {
    var trimmed = line.trim();
    if (!trimmed) return;
    if (trimmed.indexOf("#") === 0) return;
    if (trimmed.indexOf("@") === 0) return;
    if (trimmed.indexOf("model_config") === 0) return;
    if (trimmed.indexOf("def ") === 0) return;
    if (trimmed.indexOf("return ") === 0) return;
    if (trimmed.indexOf("if ") === 0) return;
    if (trimmed.indexOf("for ") === 0) return;
    if (trimmed.indexOf("raise ") === 0) return;

    var fieldMatch = trimmed.match(/^(\w+)\s*:/);
    if (!fieldMatch) return;

    var pyFieldName = fieldMatch[1];
    if (pyFieldName === "model_config" || pyFieldName === "cls" || pyFieldName === "v") return;

    var isOptional = trimmed.indexOf("Optional[") !== -1 || trimmed.indexOf("| None") !== -1;

    var aliasMatch = trimmed.match(/alias="(\w+)"/);
    var jsonName = aliasMatch ? aliasMatch[1] : pyFieldName;

    fields[jsonName] = {
      required: !isOptional,
      pythonField: pyFieldName,
    };
  });

  return fields;
}

function checkModel(schemaName, zodVarName, pydanticClassName, zodSrc, pySrc) {
  var schemaPath = path.join(SCHEMAS_DIR, schemaName + ".schema.json");

  if (!fs.existsSync(schemaPath)) {
    reportDrift(schemaName, "JSON Schema file not found: " + schemaPath);
    return;
  }

  var jsonFields = extractJsonSchemaFields(schemaPath);
  var zodFields = extractZodFields(zodSrc, zodVarName);
  var pydanticFields = extractPydanticFields(pySrc, pydanticClassName);

  if (!zodFields) {
    reportDrift(schemaName, "Zod schema '" + zodVarName + "Schema' not found in schemas.ts");
  }
  if (!pydanticFields) {
    reportDrift(schemaName, "Pydantic model '" + pydanticClassName + "' not found in schemas.py");
  }

  var jsonFieldNames = Object.keys(jsonFields);

  if (zodFields) {
    var zodFieldNames = Object.keys(zodFields);
    jsonFieldNames.forEach(function (field) {
      if (!zodFields[field]) {
        reportDrift(schemaName, "field '" + field + "' in JSON Schema but missing from Zod");
      }
    });
    zodFieldNames.forEach(function (field) {
      if (!jsonFields[field]) {
        reportDrift(schemaName, "field '" + field + "' in Zod but missing from JSON Schema");
      }
    });
  }

  if (pydanticFields) {
    var pyFieldNames = Object.keys(pydanticFields);
    jsonFieldNames.forEach(function (field) {
      if (!pydanticFields[field]) {
        reportDrift(schemaName, "field '" + field + "' in JSON Schema but missing from Pydantic");
      }
    });
    pyFieldNames.forEach(function (field) {
      if (!jsonFields[field]) {
        reportDrift(schemaName, "field '" + field + "' in Pydantic but missing from JSON Schema");
      }
    });
  }

  if (zodFields && pydanticFields) {
    jsonFieldNames.forEach(function (field) {
      var jsonReq = jsonFields[field] ? jsonFields[field].required : undefined;
      var zodReq = zodFields[field] ? zodFields[field].required : undefined;
      var pyReq = pydanticFields[field] ? pydanticFields[field].required : undefined;

      if (zodReq !== undefined && zodReq !== jsonReq) {
        reportDrift(schemaName,
          "field '" + field + "' required mismatch: JSON Schema=" + jsonReq + ", Zod=" + zodReq);
      }
      if (pyReq !== undefined && pyReq !== jsonReq) {
        reportDrift(schemaName,
          "field '" + field + "' required mismatch: JSON Schema=" + jsonReq + ", Pydantic=" + pyReq);
      }
    });
  }
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

if (!fs.existsSync(ZOD_FILE)) {
  console.error("Zod schema file not found: " + ZOD_FILE);
  process.exit(1);
}
if (!fs.existsSync(PYDANTIC_FILE)) {
  console.error("Pydantic schema file not found: " + PYDANTIC_FILE);
  process.exit(1);
}

var zodSource = fs.readFileSync(ZOD_FILE, "utf-8");
var pydanticSource = fs.readFileSync(PYDANTIC_FILE, "utf-8");

var models = [
  { schema: "artist", zod: "artist", pydantic: "Artist" },
  { schema: "piece", zod: "piece", pydantic: "Piece" },
  { schema: "collection", zod: "collection", pydantic: "Collection" },
  { schema: "mockup", zod: "mockup", pydantic: "Mockup" },
];

console.log("Checking schema drift across JSON Schema, Zod, and Pydantic...\n");

models.forEach(function (m) {
  console.log("  " + m.schema + "...");
  checkModel(m.schema, m.zod, m.pydantic, zodSource, pydanticSource);
});

// ---------------------------------------------------------------------------
// Enum value drift check
// Hardcoded expected enums act as a regression guard: if a JSON Schema enum
// is silently changed, this block fails CI before the Zod/Pydantic models
// have a chance to drift too.
// ---------------------------------------------------------------------------

var EXPECTED_ENUMS = {
  "mockup.schema.json": {
    "type": ["framed", "room", "artist-holding"]
  },
  "piece.schema.json": {
    "availabilityStatus": ["available", "low-stock", "reserved", "sold-out", "archived"]
  },
  "artist.schema.json": {
    "pricingTier": ["affordable", "mid-range", "premium"]
  }
};

console.log("\nChecking enum value drift in JSON Schema files...\n");

var enumErrors = 0;

Object.keys(EXPECTED_ENUMS).forEach(function (schemaFile) {
  var schemaPath = path.join(SCHEMAS_DIR, schemaFile);
  if (!fs.existsSync(schemaPath)) {
    console.error("  ✗ Schema file not found for enum check: " + schemaPath);
    enumErrors++;
    return;
  }

  var parsed = JSON.parse(fs.readFileSync(schemaPath, "utf-8"));
  var props = parsed.properties || {};
  var fieldChecks = EXPECTED_ENUMS[schemaFile];

  Object.keys(fieldChecks).forEach(function (field) {
    var expectedValues = fieldChecks[field];
    var prop = props[field];

    if (!prop || !prop.enum) {
      console.error("  ✗ [" + schemaFile + "] Missing enum for field \"" + field + "\"");
      enumErrors++;
      return;
    }

    var actual = prop.enum.slice().sort();
    var expected = expectedValues.slice().sort();

    if (JSON.stringify(actual) !== JSON.stringify(expected)) {
      console.error("  ✗ [" + schemaFile + "]." + field + " enum mismatch:");
      console.error("    Expected: " + JSON.stringify(expected));
      console.error("    Actual:   " + JSON.stringify(actual));
      enumErrors++;
    } else {
      console.log("  ✓ [" + schemaFile + "]." + field + " enum values match");
    }
  });
});

if (enumErrors > 0) {
  console.error("\n" + enumErrors + " enum value drift error(s) found.");
  driftFound = true;
}

if (driftFound) {
  console.error("\nDrift detected! Fix the schemas above to restore parity.\n");
  process.exit(1);
} else {
  console.log("\nAll schemas in sync. No drift detected.\n");
  process.exit(0);
}
