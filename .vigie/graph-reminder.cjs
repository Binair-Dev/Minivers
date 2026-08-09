// vigie: nudge the agent toward the code graph before Grep/Glob
let raw = ''
process.stdin.on('data', (c) => (raw += c))
process.stdin.on('end', () => {
  let pattern = ''
  try { pattern = String(JSON.parse(raw).tool_input?.pattern ?? '') } catch {}
  // literal-string greps (quoted text, log messages) stay legitimate — nudge otherwise
  const literal = /^"[^"]*"$/.test(pattern.trim())
  const out = literal ? {} : {
    hookSpecificOutput: {
      hookEventName: 'PreToolUse',
      additionalContext: 'Rappel vigie : un graphe du code est disponible. Pour toute exploration de symboles/architecture, appelle d\'abord l\'outil MCP vigie_explore (source + callers/callees + impact en un appel). Grep/Glob seulement pour du texte litteral.'
    }
  }
  process.stdout.write(JSON.stringify(out))
})
