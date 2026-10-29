import React, { useState, useEffect, useMemo, useTransition } from 'react'
import {
  Calculator,
  Sparkles,
  Zap,
  TrendingDown,
  Layers,
  FileText,
  Sliders,
  DollarSign,
  Download,
  Copy,
  Check,
  RefreshCw,
  Cpu,
  ChevronDown,
  ChevronUp,
  AlertCircle,
  ShieldCheck,
  Wand2,
} from 'lucide-react'

export default function App() {
  // Input states
  const [prompt, setPrompt] = useState(
    'Summarize this architecture overview and produce an itemized list of security controls, data flows, and risk mitigations.'
  )
  const [systemPrompt, setSystemPrompt] = useState('')
  const [showSystemPrompt, setShowSystemPrompt] = useState(false)
  const [outputTokens, setOutputTokens] = useState(500)
  const [callsPerDay, setCallsPerDay] = useState(100)
  const [cacheReadPct, setCacheReadPct] = useState(0)
  const [isBatch, setIsBatch] = useState(false)
  const [reasoningTokens, setReasoningTokens] = useState(0)
  const [providerFilter, setProviderFilter] = useState('All')

  // API states
  const [loading, setLoading] = useState(false)
  const [estimateData, setEstimateData] = useState(null)
  const [templates, setTemplates] = useState([])
  const [copied, setCopied] = useState(false)
  const [activeTab, setActiveTab] = useState('compare') // 'compare' | 'optimize'

  // Load templates on mount
  useEffect(() => {
    fetch('/api/templates')
      .then((res) => res.json())
      .then((data) => setTemplates(data))
      .catch((err) => console.error('Failed to load templates:', err))
  }, [])

  // Debounced API call to estimate costs
  useEffect(() => {
    const timer = setTimeout(() => {
      fetchEstimate()
    }, 250)
    return () => clearTimeout(timer)
  }, [prompt, systemPrompt, outputTokens, callsPerDay, cacheReadPct, isBatch, reasoningTokens, providerFilter])

  const fetchEstimate = async () => {
    if (!prompt.trim() && !systemPrompt.trim()) {
      setEstimateData(null)
      return
    }

    setLoading(true)
    try {
      const res = await fetch('/api/estimate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt,
          system_prompt: systemPrompt,
          output_tokens: Number(outputTokens),
          calls_per_day: Number(callsPerDay),
          cache_read_pct: Number(cacheReadPct) / 100,
          is_batch: Boolean(isBatch),
          reasoning_tokens: Number(reasoningTokens),
          provider_filter: providerFilter === 'All' ? null : providerFilter,
        }),
      })
      if (res.ok) {
        const data = await res.json()
        setEstimateData(data)
      }
    } catch (err) {
      console.error('Error fetching cost estimate:', err)
    } finally {
      setLoading(false)
    }
  }

  // Load a prompt template
  const applyTemplate = (tpl) => {
    setPrompt(tpl.prompt)
    if (tpl.system_prompt) {
      setSystemPrompt(tpl.system_prompt)
      setShowSystemPrompt(true)
    } else {
      setSystemPrompt('')
      setShowSystemPrompt(false)
    }
    if (tpl.output_tokens) setOutputTokens(tpl.output_tokens)
    if (tpl.calls_per_day) setCallsPerDay(tpl.calls_per_day)
    if (tpl.cache_read_pct !== undefined) setCacheReadPct(tpl.cache_read_pct * 100)
    if (tpl.reasoning_tokens) setReasoningTokens(tpl.reasoning_tokens)
  }

  // Apply prompt optimization
  const applyOptimization = () => {
    if (!estimateData?.optimization?.cleaned_preview) return
    let cleaned = prompt
    cleaned = cleaned.replace(/[ \t]+/g, ' ')
    cleaned = cleaned.replace(/\n{3,}/g, '\n\n')
    const fillers = [
      /please\s+(?:make\s+sure\s+to|be\s+sure\s+to|ensure\s+that\s+you)\b/gi,
      /as\s+an\s+ai\s+language\s+model\b/gi,
      /you\s+are\s+a\s+helpful\s+and\s+knowledgeable\s+assistant\b/gi,
      /i\s+would\s+like\s+you\s+to\b/gi,
      /could\s+you\s+please\b/gi,
      /in\s+order\s+to\b/gi,
    ]
    fillers.forEach((p) => {
      cleaned = cleaned.replace(p, '')
    })
    setPrompt(cleaned.trim())
  }

  // Copy shareable summary
  const copySummary = () => {
    if (!estimateData) return
    const text = `📊 LLM Cost Analysis Summary:
• Prompt Input Tokens: ${estimateData.token_counts.primary_input_tokens.toLocaleString()}
• Expected Output Tokens: ${estimateData.token_counts.output_tokens.toLocaleString()}
• Daily Calls: ${callsPerDay.toLocaleString()} (Monthly: ${(callsPerDay * 30).toLocaleString()})
• Cheapest Model: ${estimateData.cheapest_model?.model} ($${estimateData.cheapest_model?.single_call_cost} / call | $${estimateData.cheapest_model?.monthly_cost} / mo)
• Flagship Model: ${estimateData.flagship_model?.model} ($${estimateData.flagship_model?.single_call_cost} / call | $${estimateData.flagship_model?.monthly_cost} / mo)
${estimateData.savings_insights?.[0] ? `• Insight: ${estimateData.savings_insights[0]}` : ''}`

    navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  // Export CSV
  const exportCSV = () => {
    if (!estimateData?.models) return
    const headers = [
      'Provider',
      'Model',
      'Tier',
      'Context Window',
      'Single Call Cost ($)',
      '1K Calls Cost ($)',
      'Monthly Cost ($)',
      'Annual Cost ($)',
    ]
    const rows = estimateData.models.map((m) => [
      `"${m.provider}"`,
      `"${m.model}"`,
      `"${m.tier}"`,
      `"${m.context_window}"`,
      m.single_call_cost,
      m.thousand_calls_cost,
      m.monthly_cost,
      m.annual_cost,
    ])
    const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map((e) => e.join(','))].join('\n')
    const encodedUri = encodeURI(csvContent)
    const link = document.createElement('a')
    link.setAttribute('href', encodedUri)
    link.setAttribute('download', `llm_cost_estimate_${Date.now()}.csv`)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  // Max cost for relative visual bar calculation
  const maxSingleCost = useMemo(() => {
    if (!estimateData?.models?.length) return 1
    return Math.max(...estimateData.models.map((m) => m.single_call_cost), 0.0001)
  }, [estimateData])

  return (
    <div className="min-h-screen bg-[#090d16] text-gray-100 flex flex-col selection:bg-purple-600 selection:text-white">
      {/* Top Navbar */}
      <header className="border-b border-gray-800 bg-[#0d1322]/80 backdrop-blur-md sticky top-0 z-30 px-6 py-3.5 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-purple-600 to-indigo-500 flex items-center justify-center shadow-lg shadow-purple-500/20">
            <Calculator className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-bold text-white tracking-tight">LLM Cost Calculator Studio</h1>
              <span className="text-xs px-2 py-0.5 rounded-full font-medium bg-purple-500/10 text-purple-400 border border-purple-500/20">
                Full-Stack App
              </span>
            </div>
            <p className="text-xs text-gray-400">Accurate tokenization, caching, batching & side-by-side cost comparisons</p>
          </div>
        </div>

        {/* Quick action buttons */}
        <div className="flex items-center gap-2">
          <button
            onClick={copySummary}
            disabled={!estimateData}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-200 transition border border-gray-700 disabled:opacity-50"
            title="Copy summary to clipboard"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
            {copied ? 'Copied!' : 'Copy Summary'}
          </button>
          <button
            onClick={exportCSV}
            disabled={!estimateData}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white transition shadow-sm disabled:opacity-50"
            title="Download CSV table"
          >
            <Download className="w-3.5 h-3.5" />
            Export CSV
          </button>
        </div>
      </header>

      {/* Template Bar */}
      <div className="border-b border-gray-800/80 bg-[#0b101e] px-6 py-2.5 flex items-center gap-2 overflow-x-auto text-xs">
        <span className="text-gray-400 font-semibold flex items-center gap-1 shrink-0 mr-1">
          <Sparkles className="w-3.5 h-3.5 text-amber-400" /> Templates:
        </span>
        {templates.map((tpl) => (
          <button
            key={tpl.id}
            onClick={() => applyTemplate(tpl)}
            className="px-2.5 py-1 rounded-md bg-gray-800/60 hover:bg-gray-700/80 text-gray-300 border border-gray-700/50 shrink-0 transition"
          >
            {tpl.name}
          </button>
        ))}
        <button
          onClick={() => {
            setPrompt('')
            setSystemPrompt('')
          }}
          className="px-2 py-1 rounded-md text-gray-500 hover:text-gray-300 shrink-0 ml-auto transition"
        >
          Clear
        </button>
      </div>

      {/* Main Content Layout */}
      <main className="flex-1 max-w-[1700px] w-full mx-auto p-4 md:p-6 grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Prompt Studio & Sliders (5 cols on lg) */}
        <div className="lg:col-span-5 flex flex-col gap-5">
          {/* Prompt Editor Card */}
          <div className="bg-[#111728] border border-gray-800 rounded-2xl p-5 shadow-xl flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4 text-purple-400" />
                <h2 className="text-sm font-semibold text-gray-200 uppercase tracking-wider">Prompt Studio</h2>
              </div>
              <button
                onClick={() => setShowSystemPrompt(!showSystemPrompt)}
                className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center gap-1 transition"
              >
                {showSystemPrompt ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                {showSystemPrompt ? 'Hide System Prompt' : '+ Add System Prompt'}
              </button>
            </div>

            {/* Optional System Prompt Field */}
            {showSystemPrompt && (
              <div className="flex flex-col gap-1.5 animate-fadeIn">
                <label className="text-xs font-medium text-gray-400 flex items-center justify-between">
                  <span>System Instructions / Persona</span>
                  <span className="text-[10px] text-gray-500">Cached if enabled</span>
                </label>
                <textarea
                  rows={2}
                  value={systemPrompt}
                  onChange={(e) => setSystemPrompt(e.target.value)}
                  placeholder="You are an expert software engineer... (System directives, rules, guardrails)"
                  className="w-full bg-[#0a0f1d] border border-gray-700/80 rounded-xl p-3 text-xs text-gray-200 placeholder-gray-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 font-mono resize-y"
                />
              </div>
            )}

            {/* Main User Prompt Field */}
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-medium text-gray-300 flex items-center justify-between">
                <span>User Prompt / Input Payload</span>
                <span className="text-xs text-indigo-400 font-mono">
                  {estimateData ? `${estimateData.token_counts.primary_input_tokens.toLocaleString()} tokens` : '0 tokens'}
                </span>
              </label>
              <textarea
                rows={7}
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Enter or paste your prompt, document, or code context here..."
                className="w-full bg-[#0a0f1d] border border-gray-700/80 rounded-xl p-3.5 text-xs text-gray-100 placeholder-gray-500 focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500 font-mono resize-y"
              />
            </div>

            {/* Live Text Metrics Bar */}
            {estimateData && (
              <div className="grid grid-cols-4 gap-2 pt-2 border-t border-gray-800 text-center">
                <div className="bg-[#0b101e] py-1.5 px-2 rounded-lg border border-gray-800/80">
                  <div className="text-[10px] text-gray-400 uppercase">Input Tokens</div>
                  <div className="text-xs font-bold text-purple-400 font-mono">
                    {estimateData.token_counts.primary_input_tokens.toLocaleString()}
                  </div>
                </div>
                <div className="bg-[#0b101e] py-1.5 px-2 rounded-lg border border-gray-800/80">
                  <div className="text-[10px] text-gray-400 uppercase">Characters</div>
                  <div className="text-xs font-semibold text-gray-300 font-mono">
                    {estimateData.text_stats.characters.toLocaleString()}
                  </div>
                </div>
                <div className="bg-[#0b101e] py-1.5 px-2 rounded-lg border border-gray-800/80">
                  <div className="text-[10px] text-gray-400 uppercase">Words</div>
                  <div className="text-xs font-semibold text-gray-300 font-mono">
                    {estimateData.text_stats.words.toLocaleString()}
                  </div>
                </div>
                <div className="bg-[#0b101e] py-1.5 px-2 rounded-lg border border-gray-800/80">
                  <div className="text-[10px] text-gray-400 uppercase">Total / Call</div>
                  <div className="text-xs font-bold text-emerald-400 font-mono">
                    {estimateData.token_counts.total_tokens_per_call.toLocaleString()}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Simulation & Cost Controls Card */}
          <div className="bg-[#111728] border border-gray-800 rounded-2xl p-5 shadow-xl flex flex-col gap-4">
            <div className="flex items-center gap-2">
              <Sliders className="w-4 h-4 text-indigo-400" />
              <h2 className="text-sm font-semibold text-gray-200 uppercase tracking-wider">Simulation Parameters</h2>
            </div>

            {/* Expected Output Tokens */}
            <div className="flex flex-col gap-1.5">
              <div className="flex justify-between text-xs">
                <span className="text-gray-300 font-medium">Expected Output Tokens:</span>
                <span className="text-amber-400 font-mono font-bold">{outputTokens.toLocaleString()} tokens</span>
              </div>
              <input
                type="range"
                min="50"
                max="8000"
                step="50"
                value={outputTokens}
                onChange={(e) => setOutputTokens(Number(e.target.value))}
                className="w-full accent-amber-500 cursor-pointer"
              />
              <div className="flex gap-1.5 mt-1">
                {[150, 500, 1500, 4000].map((preset) => (
                  <button
                    key={preset}
                    onClick={() => setOutputTokens(preset)}
                    className={`px-2 py-0.5 rounded text-[11px] transition ${
                      outputTokens === preset ? 'bg-amber-500 text-gray-900 font-semibold' : 'bg-gray-800 text-gray-400 hover:text-gray-200'
                    }`}
                  >
                    {preset === 150 ? 'Short (150)' : preset === 500 ? 'Standard (500)' : preset === 1500 ? 'Long (1.5K)' : 'Deep (4K)'}
                  </button>
                ))}
              </div>
            </div>

            {/* Daily Call Volume */}
            <div className="flex flex-col gap-1.5 pt-2 border-t border-gray-800/80">
              <div className="flex justify-between text-xs">
                <span className="text-gray-300 font-medium">Calls Per Day:</span>
                <span className="text-cyan-400 font-mono font-bold">
                  {callsPerDay.toLocaleString()} <span className="text-gray-400 font-normal">({(callsPerDay * 30).toLocaleString()}/mo)</span>
                </span>
              </div>
              <input
                type="range"
                min="10"
                max="50000"
                step="10"
                value={callsPerDay}
                onChange={(e) => setCallsPerDay(Number(e.target.value))}
                className="w-full accent-cyan-500 cursor-pointer"
              />
              <div className="flex gap-1.5 mt-1">
                {[100, 1000, 5000, 20000].map((preset) => (
                  <button
                    key={preset}
                    onClick={() => setCallsPerDay(preset)}
                    className={`px-2 py-0.5 rounded text-[11px] transition ${
                      callsPerDay === preset ? 'bg-cyan-500 text-gray-900 font-semibold' : 'bg-gray-800 text-gray-400 hover:text-gray-200'
                    }`}
                  >
                    {preset < 1000 ? `${preset}/day` : `${preset / 1000}K/day`}
                  </button>
                ))}
              </div>
            </div>

            {/* Advanced Mechanics: Caching & Batching */}
            <div className="pt-2 border-t border-gray-800/80 flex flex-col gap-3">
              {/* Prompt Caching Slider */}
              <div className="flex flex-col gap-1">
                <div className="flex justify-between text-xs">
                  <span className="text-gray-300 font-medium flex items-center gap-1.5">
                    <Zap className="w-3.5 h-3.5 text-emerald-400" /> Prompt Cache Hit Rate:
                  </span>
                  <span className="text-emerald-400 font-mono font-bold">{cacheReadPct}%</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="100"
                  step="5"
                  value={cacheReadPct}
                  onChange={(e) => setCacheReadPct(Number(e.target.value))}
                  className="w-full accent-emerald-500 cursor-pointer"
                />
                <p className="text-[10px] text-gray-500">
                  Simulates discounts on cached context (e.g., Claude 90% off, Gemini context caching, OpenAI cache).
                </p>
              </div>

              {/* Batch API Toggle */}
              <div className="flex items-center justify-between p-2.5 rounded-xl bg-[#0b101e] border border-gray-800">
                <div className="flex flex-col">
                  <span className="text-xs font-medium text-gray-200 flex items-center gap-1.5">
                    <Layers className="w-3.5 h-3.5 text-blue-400" /> Asynchronous Batch API
                  </span>
                  <span className="text-[10px] text-gray-400">Applies 50% discount for off-peak 24h turnaround</span>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={isBatch}
                    onChange={(e) => setIsBatch(e.target.checked)}
                    className="sr-only peer"
                  />
                  <div className="w-9 h-5 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-blue-600"></div>
                </label>
              </div>

              {/* Reasoning Tokens Slider */}
              <div className="flex flex-col gap-1">
                <div className="flex justify-between text-xs">
                  <span className="text-gray-300 font-medium flex items-center gap-1.5">
                    <Cpu className="w-3.5 h-3.5 text-pink-400" /> Reasoning / Thinking Tokens:
                  </span>
                  <span className="text-pink-400 font-mono font-bold">{reasoningTokens.toLocaleString()} tokens</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="16000"
                  step="200"
                  value={reasoningTokens}
                  onChange={(e) => setReasoningTokens(Number(e.target.value))}
                  className="w-full accent-pink-500 cursor-pointer"
                />
                <p className="text-[10px] text-gray-500">
                  Billed at output rates for reasoning models (Claude 3.7 Thinking Mode, OpenAI o1/o3-mini, DeepSeek R1).
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Model Comparison, Analytics & Optimization (7 cols on lg) */}
        <div className="lg:col-span-7 flex flex-col gap-5">
          {/* Top KPI Cards */}
          {estimateData && (
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {/* Cheapest Card */}
              <div className="bg-gradient-to-br from-[#101b1e] to-[#0d1624] border border-emerald-500/20 rounded-2xl p-4 shadow-lg flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between text-xs text-emerald-400 font-semibold uppercase tracking-wider mb-1">
                    <span className="flex items-center gap-1">
                      <TrendingDown className="w-3.5 h-3.5" /> Most Economical
                    </span>
                    <span className="text-[10px] bg-emerald-500/10 px-1.5 py-0.5 rounded text-emerald-300">
                      {estimateData.cheapest_model?.provider}
                    </span>
                  </div>
                  <div className="text-base font-bold text-white truncate">{estimateData.cheapest_model?.model}</div>
                </div>
                <div className="mt-3 pt-2 border-t border-emerald-500/10 flex items-baseline justify-between">
                  <span className="text-xs text-gray-400">Single call:</span>
                  <span className="text-sm font-mono font-bold text-emerald-400">
                    ${estimateData.cheapest_model?.single_call_cost.toFixed(6)}
                  </span>
                </div>
                <div className="flex items-baseline justify-between text-xs">
                  <span className="text-gray-400">Monthly spend:</span>
                  <span className="font-mono font-bold text-white">
                    ${estimateData.cheapest_model?.monthly_cost.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </span>
                </div>
              </div>

              {/* Flagship Reference Card */}
              <div className="bg-gradient-to-br from-[#1e1526] to-[#140e1e] border border-purple-500/20 rounded-2xl p-4 shadow-lg flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between text-xs text-purple-400 font-semibold uppercase tracking-wider mb-1">
                    <span className="flex items-center gap-1">
                      <Sparkles className="w-3.5 h-3.5" /> Flagship Baseline
                    </span>
                    <span className="text-[10px] bg-purple-500/10 px-1.5 py-0.5 rounded text-purple-300">
                      {estimateData.flagship_model?.provider}
                    </span>
                  </div>
                  <div className="text-base font-bold text-white truncate">{estimateData.flagship_model?.model}</div>
                </div>
                <div className="mt-3 pt-2 border-t border-purple-500/10 flex items-baseline justify-between">
                  <span className="text-xs text-gray-400">Single call:</span>
                  <span className="text-sm font-mono font-bold text-purple-400">
                    ${estimateData.flagship_model?.single_call_cost.toFixed(6)}
                  </span>
                </div>
                <div className="flex items-baseline justify-between text-xs">
                  <span className="text-gray-400">Monthly spend:</span>
                  <span className="font-mono font-bold text-white">
                    ${estimateData.flagship_model?.monthly_cost.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </span>
                </div>
              </div>

              {/* Monthly Savings Card */}
              <div className="bg-gradient-to-br from-[#171b29] to-[#0f1422] border border-indigo-500/20 rounded-2xl p-4 shadow-lg flex flex-col justify-between">
                <div>
                  <div className="text-xs text-indigo-400 font-semibold uppercase tracking-wider mb-1 flex items-center gap-1">
                    <DollarSign className="w-3.5 h-3.5" /> Potential Savings
                  </div>
                  <div className="text-base font-bold text-white">
                    {estimateData.cheapest_model && estimateData.flagship_model
                      ? `$${Math.max(
                          0,
                          estimateData.flagship_model.monthly_cost - estimateData.cheapest_model.monthly_cost
                        ).toLocaleString(undefined, { minimumFractionDigits: 2 })}/mo`
                      : '$0.00'}
                  </div>
                </div>
                <div className="mt-2 text-[11px] text-gray-400 leading-tight">
                  {estimateData.savings_insights?.[0] ? (
                    <span>By routing prompts to efficient models over flagship tier.</span>
                  ) : (
                    <span>Comparing multi-provider cost spreads.</span>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Actionable Insights Alert */}
          {estimateData?.savings_insights?.length > 0 && (
            <div className="bg-gradient-to-r from-indigo-950/40 via-purple-950/30 to-blue-950/40 border border-indigo-800/40 rounded-xl p-3.5 text-xs text-indigo-200 flex items-start gap-2.5">
              <Sparkles className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
              <div className="flex-1 space-y-1">
                {estimateData.savings_insights.map((insight, idx) => (
                  <p key={idx} dangerouslySetInnerHTML={{ __html: insight.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') }} />
                ))}
              </div>
            </div>
          )}

          {/* Tab Navigation: Comparison Table vs Prompt Optimizer */}
          <div className="bg-[#111728] border border-gray-800 rounded-2xl p-5 shadow-xl flex flex-col gap-4">
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-gray-800 pb-3">
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setActiveTab('compare')}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                    activeTab === 'compare' ? 'bg-purple-600 text-white' : 'bg-gray-800/60 text-gray-400 hover:text-gray-200'
                  }`}
                >
                  Cost Comparison Matrix
                </button>
                <button
                  onClick={() => setActiveTab('optimize')}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition ${
                    activeTab === 'optimize' ? 'bg-indigo-600 text-white' : 'bg-gray-800/60 text-gray-400 hover:text-gray-200'
                  }`}
                >
                  <Wand2 className="w-3.5 h-3.5" /> Prompt Optimizer
                  {estimateData?.optimization?.tokens_saved > 0 && (
                    <span className="bg-emerald-500 text-gray-900 font-bold px-1.5 py-0.2 rounded-full text-[10px]">
                      -{estimateData.optimization.tokens_saved} tok
                    </span>
                  )}
                </button>
              </div>

              {/* Provider Filter Badges */}
              {activeTab === 'compare' && (
                <div className="flex items-center gap-1 overflow-x-auto text-[11px]">
                  {['All', 'Google', 'OpenAI', 'Anthropic', 'DeepSeek', 'Meta', 'Mistral'].map((p) => (
                    <button
                      key={p}
                      onClick={() => setProviderFilter(p)}
                      className={`px-2 py-0.5 rounded-md transition ${
                        providerFilter === p
                          ? 'bg-gray-200 text-gray-900 font-bold'
                          : 'bg-gray-800 text-gray-400 hover:text-gray-200'
                      }`}
                    >
                      {p}
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* TAB 1: Comparison Matrix */}
            {activeTab === 'compare' && (
              <div className="flex flex-col gap-3">
                {loading && (
                  <div className="flex items-center justify-center py-8 text-xs text-gray-400 gap-2">
                    <RefreshCw className="w-4 h-4 animate-spin text-purple-400" />
                    Calculating multi-provider token metrics...
                  </div>
                )}

                {!loading && estimateData?.models && (
                  /* Compliant with modern-web-guidance responsive table with sticky headers & container queries */
                  <div
                    tabIndex={0}
                    role="region"
                    aria-labelledby="cost-table-caption"
                    className="table-wrapper border border-gray-800 rounded-xl"
                  >
                    <table>
                      <caption id="cost-table-caption" className="sr-only">
                        LLM API Cost Comparison Table Across Providers
                      </caption>
                      <thead>
                        <tr className="border-b border-gray-800 text-[11px] text-gray-400 uppercase tracking-wider text-left">
                          <th className="py-2.5 px-3">Model & Provider</th>
                          <th className="py-2.5 px-2">Context</th>
                          <th className="py-2.5 px-3 text-right">Cost / 1 Call</th>
                          <th className="py-2.5 px-3 text-right">Cost / 1K</th>
                          <th className="py-2.5 px-3 text-right">Monthly (30d)</th>
                          <th className="py-2.5 px-3 text-center">Cost Scale</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-800/60 text-xs">
                        {estimateData.models.map((model) => {
                          const relativeWidth = Math.max(4, Math.min(100, (model.single_call_cost / maxSingleCost) * 100))
                          return (
                            <tr key={`${model.provider}-${model.model}`} className="hover:bg-gray-800/30 transition">
                              {/* Row header remains sticky on desktop, cards on mobile */}
                              <th className="py-2.5 px-3 font-normal text-left">
                                <div className="flex items-center gap-2">
                                  <span
                                    className={`w-1.5 h-1.5 rounded-full ${
                                      model.provider === 'Google'
                                        ? 'bg-blue-400'
                                        : model.provider === 'OpenAI'
                                        ? 'bg-emerald-400'
                                        : model.provider === 'Anthropic'
                                        ? 'bg-amber-400'
                                        : model.provider === 'DeepSeek'
                                        ? 'bg-cyan-400'
                                        : 'bg-purple-400'
                                    }`}
                                  />
                                  <span className="font-semibold text-gray-100">{model.model}</span>
                                  <span className="text-[10px] text-gray-400 font-mono">({model.provider})</span>
                                </div>
                                <div className="text-[10px] text-gray-400 ml-3.5 mt-0.5">{model.tier}</div>
                              </th>
                              <td className="py-2.5 px-2 text-gray-300 font-mono text-[11px]">{model.context_window}</td>
                              <td className="py-2.5 px-3 text-right font-mono font-medium text-emerald-400">
                                ${model.single_call_cost.toFixed(6)}
                              </td>
                              <td className="py-2.5 px-3 text-right font-mono text-gray-300">
                                ${model.thousand_calls_cost.toFixed(4)}
                              </td>
                              <td className="py-2.5 px-3 text-right font-mono font-bold text-purple-300">
                                ${model.monthly_cost.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                              </td>
                              <td className="py-2.5 px-3">
                                <div className="w-full bg-gray-800 h-2 rounded-full overflow-hidden flex items-center">
                                  <div
                                    className={`h-full rounded-full ${
                                      model.single_call_cost === estimateData.cheapest_model?.single_call_cost
                                        ? 'bg-emerald-400'
                                        : 'bg-indigo-500'
                                    }`}
                                    style={{ width: `${relativeWidth}%` }}
                                  />
                                </div>
                              </td>
                            </tr>
                          )
                        })}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}

            {/* TAB 2: Prompt Optimizer & Token Trimmer */}
            {activeTab === 'optimize' && estimateData?.optimization && (
              <div className="flex flex-col gap-4 text-xs">
                <div className="p-4 rounded-xl bg-[#0b101e] border border-gray-800 flex items-start justify-between gap-4">
                  <div>
                    <h3 className="font-semibold text-gray-200 flex items-center gap-1.5 text-sm">
                      <Sparkles className="w-4 h-4 text-amber-400" /> Token Optimization Analysis
                    </h3>
                    <p className="text-gray-400 mt-1">
                      Scans your prompt for conversational filler, redundant whitespace, and duplicate instructions that burn
                      tokens needlessly.
                    </p>
                  </div>
                  <div className="text-right shrink-0">
                    <div className="text-2xl font-bold font-mono text-emerald-400">
                      -{estimateData.optimization.percentage_saved}%
                    </div>
                    <div className="text-[10px] text-gray-400">
                      {estimateData.optimization.tokens_saved} tokens trimmable
                    </div>
                  </div>
                </div>

                {estimateData.optimization.suggestions.length > 0 ? (
                  <div className="space-y-2">
                    <h4 className="font-medium text-gray-300 uppercase tracking-wider text-[11px]">Detected Opportunities:</h4>
                    {estimateData.optimization.suggestions.map((s, idx) => (
                      <div key={idx} className="p-3 rounded-lg bg-gray-800/40 border border-gray-700/60 flex items-start gap-2.5">
                        <AlertCircle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                        <div className="flex-1">
                          <span className="font-semibold text-gray-200">{s.type}:</span> {s.message}
                        </div>
                      </div>
                    ))}
                    <button
                      onClick={applyOptimization}
                      className="mt-2 w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-medium flex items-center justify-center gap-2 transition shadow-lg"
                    >
                      <Wand2 className="w-4 h-4" /> Apply Optimization & Trim Prompt
                    </button>
                  </div>
                ) : (
                  <div className="p-6 text-center text-gray-400 bg-gray-800/20 rounded-xl border border-gray-800">
                    <ShieldCheck className="w-8 h-8 text-emerald-400 mx-auto mb-2" />
                    Prompt is cleanly structured! No significant token bloat detected.
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}
