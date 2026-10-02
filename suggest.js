import { loadSnapshot } from "./src/catalog.js";
import { loadQueries, validateQuery } from "./src/queries.js";
import { Suggester } from "./src/suggester.js";

const argv = process.argv.slice(2);
if (argv.includes("--help") || argv.length === 0) {
  console.log("node suggest.js <validate|resolve> --terms PATH --aliases PATH --queries PATH");
} else {
  const command = argv[0];
  const options = {};
  for (let i = 1; i < argv.length; i += 2) {
    options[argv[i].replace(/^--/, "")] = argv[i + 1];
  }

  const snapshot = loadSnapshot(options.terms, options.aliases);
  const queries = loadQueries(options.queries);

  if (command === "validate") {
    const checks = queries.map(validateQuery);
    console.log(JSON.stringify({
      terms: snapshot.terms.size,
      aliases: snapshot.aliasCount,
      queries: queries.length,
      valid_queries: checks.filter((item) => item.ok).length,
      invalid_queries: checks.filter((item) => !item.ok).length
    }));
  } else if (command === "resolve") {
    const suggester = new Suggester(snapshot);
    for (const raw of queries) {
      const checked = validateQuery(raw);
      if (!checked.ok) {
        console.log(JSON.stringify({
          request_id: checked.requestId,
          status: "invalid",
          reason: "invalid_query"
        }));
      } else {
        console.log(JSON.stringify({
          request_id: checked.query.requestId,
          status: "resolved",
          suggestions: suggester.resolve(checked.query)
        }));
      }
    }
  } else {
    throw new Error("unknown command");
  }
}
