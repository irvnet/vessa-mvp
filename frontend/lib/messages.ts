export function getMessageText(content: unknown): string {
  if (typeof content === "string") return content;
  if (Array.isArray(content)) {
    return content
      .map((block) => {
        if (typeof block === "string") return block;
        if (block && typeof block === "object" && "text" in block) {
          return String((block as { text?: unknown }).text ?? "");
        }
        return "";
      })
      .join("");
  }
  return "";
}

export type Citations = {
  body: string;
  cases: string[];
  sources: string[];
};

// The agent appends provenance inline as "(Case: X)" / "(Source: Y.pdf)".
// Lift those out of the prose so we can render them as citation chips and
// keep the answer body clean. Falls back gracefully when none are present.
export function extractCitations(text: string): Citations {
  const cases: string[] = [];
  const sources: string[] = [];

  const caseRe = /\(Case:\s*([^)]+)\)/gi;
  const sourceRe = /\(Source:\s*([^)]+)\)/gi;

  let m: RegExpExecArray | null;
  while ((m = caseRe.exec(text))) {
    const v = m[1].trim();
    if (v && !cases.includes(v)) cases.push(v);
  }
  while ((m = sourceRe.exec(text))) {
    const v = m[1].trim();
    if (v && !sources.includes(v)) sources.push(v);
  }

  const body = text
    .replace(caseRe, "")
    .replace(sourceRe, "")
    // tidy the whitespace / dangling punctuation the removals leave behind
    .replace(/[ \t]{2,}/g, " ")
    .replace(/\s+([.,;])/g, "$1")
    .replace(/\(\s*\)/g, "")
    .trim();

  return { body, cases, sources };
}

export function toolLabel(name?: string): string {
  switch (name) {
    case "search_agendas":
      return "Agenda search";
    case "retrieve_information":
      return "Knowledge base";
    case "tavily_search":
    case "tavily_search_results_json":
      return "Web search";
    case "arxiv":
      return "Arxiv";
    default:
      return name ?? "tool";
  }
}
