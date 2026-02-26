import { useState } from 'react'
import { 
  Upload, 
  FileText, 
  Terminal, 
  AlertCircle, 
  CheckCircle, 
  Loader2,
  ChevronDown,
  ChevronUp,
  Copy,
  Check,
  Server
} from 'lucide-react'

function App() {
  const [describeOutput, setDescribeOutput] = useState('')
  const [podLogs, setPodLogs] = useState('')
  const [deploymentYaml, setDeploymentYaml] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [expandedSections, setExpandedSections] = useState({
    logAnalysis: true,
    yamlValidation: true,
    ragContext: false
  })
  const [copiedCommand, setCopiedCommand] = useState(null)

  const handleFileUpload = (e, setter) => {
    const file = e.target.files[0]
    if (file) {
      const reader = new FileReader()
      reader.onload = (event) => {
        setter(event.target.result)
      }
      reader.readAsText(file)
    }
  }

  const handleAnalyze = async () => {
    if (!describeOutput || !podLogs || !deploymentYaml) {
      setError('Please fill in all fields')
      return
    }

    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const response = await fetch('/api/v1/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          describe_output: describeOutput,
          pod_logs: podLogs,
          deployment_yaml: deploymentYaml
        })
      })

      if (!response.ok) {
        const errData = await response.json()
        throw new Error(errData.detail?.error || 'Analysis failed')
      }

      const data = await response.json()
      setResult(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const toggleSection = (section) => {
    setExpandedSections(prev => ({ ...prev, [section]: !prev[section] }))
  }

  const copyCommand = (cmd, index) => {
    navigator.clipboard.writeText(cmd)
    setCopiedCommand(index)
    setTimeout(() => setCopiedCommand(null), 2000)
  }

  const getSeverityColor = (severity) => {
    const colors = {
      critical: 'bg-red-100 text-red-800 border-red-200',
      high: 'bg-orange-100 text-orange-800 border-orange-200',
      medium: 'bg-yellow-100 text-yellow-800 border-yellow-200',
      low: 'bg-blue-100 text-blue-800 border-blue-200',
      info: 'bg-gray-100 text-gray-800 border-gray-200'
    }
    return colors[severity] || colors.info
  }

  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.8) return 'text-green-600'
    if (confidence >= 0.6) return 'text-yellow-600'
    return 'text-red-600'
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-3 mb-2">
            <Server className="w-10 h-10 text-blue-400" />
            <h1 className="text-4xl font-bold text-white">K8s AI Troubleshooter</h1>
          </div>
          <p className="text-slate-400">Multi-Agent Kubernetes Issue Analysis</p>
        </div>

        <div className="grid lg:grid-cols-2 gap-6">
          {/* Input Section */}
          <div className="space-y-4">
            {/* Describe Output */}
            <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
              <div className="flex items-center justify-between mb-3">
                <label className="flex items-center gap-2 text-sm font-medium text-slate-200">
                  <Terminal className="w-4 h-4 text-blue-400" />
                  kubectl describe pod output
                </label>
                <label className="cursor-pointer text-xs bg-slate-700 hover:bg-slate-600 text-slate-300 px-3 py-1 rounded-lg transition">
                  <input
                    type="file"
                    className="hidden"
                    accept=".txt,.log"
                    onChange={(e) => handleFileUpload(e, setDescribeOutput)}
                  />
                  Upload file
                </label>
              </div>
              <textarea
                className="w-full h-32 bg-slate-900 text-slate-100 text-sm font-mono rounded-lg p-3 border border-slate-600 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none resize-none"
                placeholder="Paste output from: kubectl describe pod <pod-name>"
                value={describeOutput}
                onChange={(e) => setDescribeOutput(e.target.value)}
              />
            </div>

            {/* Pod Logs */}
            <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
              <div className="flex items-center justify-between mb-3">
                <label className="flex items-center gap-2 text-sm font-medium text-slate-200">
                  <FileText className="w-4 h-4 text-green-400" />
                  Pod Logs
                </label>
                <label className="cursor-pointer text-xs bg-slate-700 hover:bg-slate-600 text-slate-300 px-3 py-1 rounded-lg transition">
                  <input
                    type="file"
                    className="hidden"
                    accept=".txt,.log"
                    onChange={(e) => handleFileUpload(e, setPodLogs)}
                  />
                  Upload file
                </label>
              </div>
              <textarea
                className="w-full h-32 bg-slate-900 text-slate-100 text-sm font-mono rounded-lg p-3 border border-slate-600 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none resize-none"
                placeholder="Paste output from: kubectl logs <pod-name>"
                value={podLogs}
                onChange={(e) => setPodLogs(e.target.value)}
              />
            </div>

            {/* Deployment YAML */}
            <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
              <div className="flex items-center justify-between mb-3">
                <label className="flex items-center gap-2 text-sm font-medium text-slate-200">
                  <Upload className="w-4 h-4 text-purple-400" />
                  Deployment YAML
                </label>
                <label className="cursor-pointer text-xs bg-slate-700 hover:bg-slate-600 text-slate-300 px-3 py-1 rounded-lg transition">
                  <input
                    type="file"
                    className="hidden"
                    accept=".yaml,.yml"
                    onChange={(e) => handleFileUpload(e, setDeploymentYaml)}
                  />
                  Upload YAML
                </label>
              </div>
              <textarea
                className="w-full h-32 bg-slate-900 text-slate-100 text-sm font-mono rounded-lg p-3 border border-slate-600 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none resize-none"
                placeholder="Paste your deployment YAML configuration"
                value={deploymentYaml}
                onChange={(e) => setDeploymentYaml(e.target.value)}
              />
            </div>

            {/* Analyze Button */}
            <button
              onClick={handleAnalyze}
              disabled={loading}
              className="w-full py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 text-white font-medium rounded-xl transition flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  <AlertCircle className="w-5 h-5" />
                  Analyze Issue
                </>
              )}
            </button>

            {error && (
              <div className="bg-red-900/50 border border-red-700 text-red-200 px-4 py-3 rounded-xl">
                {error}
              </div>
            )}
          </div>

          {/* Results Section */}
          <div className="space-y-4">
            {!result && !loading && (
              <div className="bg-slate-800 rounded-xl p-8 border border-slate-700 text-center">
                <Server className="w-16 h-16 text-slate-600 mx-auto mb-4" />
                <p className="text-slate-400">Analysis results will appear here</p>
                <p className="text-slate-500 text-sm mt-2">Fill in the inputs and click Analyze</p>
              </div>
            )}

            {loading && (
              <div className="bg-slate-800 rounded-xl p-8 border border-slate-700 text-center">
                <Loader2 className="w-16 h-16 text-blue-400 mx-auto mb-4 animate-spin" />
                <p className="text-slate-300">Analyzing your Kubernetes issue...</p>
                <p className="text-slate-500 text-sm mt-2">This may take 10-30 seconds</p>
              </div>
            )}

            {result && (
              <div className="space-y-4">
                {/* Main Result Card */}
                <div className="bg-slate-800 rounded-xl p-5 border border-slate-700">
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <span className="inline-block px-3 py-1 bg-red-900/50 text-red-300 text-sm font-medium rounded-full mb-2">
                        {result.error_category}
                      </span>
                      <h2 className="text-xl font-semibold text-white">{result.root_cause}</h2>
                    </div>
                    <div className={`text-right ${getConfidenceColor(result.confidence)}`}>
                      <div className="text-2xl font-bold">{(result.confidence * 100).toFixed(0)}%</div>
                      <div className="text-xs">confidence</div>
                    </div>
                  </div>
                  <p className="text-slate-300 text-sm leading-relaxed">{result.explanation}</p>
                </div>

                {/* Fix Steps */}
                <div className="bg-slate-800 rounded-xl p-5 border border-slate-700">
                  <h3 className="flex items-center gap-2 text-lg font-medium text-white mb-3">
                    <CheckCircle className="w-5 h-5 text-green-400" />
                    Fix Steps
                  </h3>
                  <ol className="space-y-2">
                    {result.fix_steps.map((step, i) => (
                      <li key={i} className="flex gap-3 text-sm text-slate-300">
                        <span className="flex-shrink-0 w-6 h-6 bg-slate-700 rounded-full flex items-center justify-center text-xs font-medium">
                          {i + 1}
                        </span>
                        <span>{step}</span>
                      </li>
                    ))}
                  </ol>
                </div>

                {/* kubectl Commands */}
                <div className="bg-slate-800 rounded-xl p-5 border border-slate-700">
                  <h3 className="flex items-center gap-2 text-lg font-medium text-white mb-3">
                    <Terminal className="w-5 h-5 text-blue-400" />
                    Suggested Commands
                  </h3>
                  <div className="space-y-2">
                    {result.kubectl_commands.map((cmd, i) => (
                      <div key={i} className="flex items-center justify-between bg-slate-900 rounded-lg px-3 py-2 group">
                        <code className="text-sm text-green-400 font-mono">{cmd}</code>
                        <button
                          onClick={() => copyCommand(cmd, i)}
                          className="text-slate-500 hover:text-white transition"
                        >
                          {copiedCommand === i ? (
                            <Check className="w-4 h-4 text-green-400" />
                          ) : (
                            <Copy className="w-4 h-4" />
                          )}
                        </button>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Log Analysis */}
                <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
                  <button
                    onClick={() => toggleSection('logAnalysis')}
                    className="w-full flex items-center justify-between p-4 text-left hover:bg-slate-700/50 transition"
                  >
                    <span className="font-medium text-white">Log Analysis Details</span>
                    {expandedSections.logAnalysis ? (
                      <ChevronUp className="w-5 h-5 text-slate-400" />
                    ) : (
                      <ChevronDown className="w-5 h-5 text-slate-400" />
                    )}
                  </button>
                  {expandedSections.logAnalysis && (
                    <div className="px-4 pb-4 space-y-3">
                      <div className="flex justify-between text-sm">
                        <span className="text-slate-400">Confidence:</span>
                        <span className={getConfidenceColor(result.log_analysis.confidence)}>
                          {(result.log_analysis.confidence * 100).toFixed(0)}%
                        </span>
                      </div>
                      <div>
                        <span className="text-slate-400 text-sm">Probable Cause:</span>
                        <p className="text-slate-200 text-sm mt-1">{result.log_analysis.probable_cause}</p>
                      </div>
                      {result.log_analysis.supporting_log_lines.length > 0 && (
                        <div>
                          <span className="text-slate-400 text-sm">Supporting Log Lines:</span>
                          <div className="mt-1 space-y-1">
                            {result.log_analysis.supporting_log_lines.map((line, i) => (
                              <code key={i} className="block text-xs bg-slate-900 text-red-400 p-2 rounded font-mono">
                                {line}
                              </code>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>

                {/* YAML Validation */}
                <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
                  <button
                    onClick={() => toggleSection('yamlValidation')}
                    className="w-full flex items-center justify-between p-4 text-left hover:bg-slate-700/50 transition"
                  >
                    <span className="font-medium text-white">
                      YAML Validation ({result.yaml_validation.misconfigurations.length} issues)
                    </span>
                    {expandedSections.yamlValidation ? (
                      <ChevronUp className="w-5 h-5 text-slate-400" />
                    ) : (
                      <ChevronDown className="w-5 h-5 text-slate-400" />
                    )}
                  </button>
                  {expandedSections.yamlValidation && (
                    <div className="px-4 pb-4 space-y-2">
                      {result.yaml_validation.misconfigurations.map((issue, i) => (
                        <div key={i} className={`p-3 rounded-lg border ${getSeverityColor(issue.severity)}`}>
                          <div className="flex items-center gap-2 mb-1">
                            <span className="text-xs font-medium uppercase">{issue.severity}</span>
                            {issue.field_path && (
                              <code className="text-xs opacity-70">{issue.field_path}</code>
                            )}
                          </div>
                          <p className="text-sm font-medium">{issue.issue}</p>
                          <p className="text-xs mt-1 opacity-80">{issue.recommendation}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* RAG Context */}
                {result.rag_context_used.length > 0 && (
                  <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
                    <button
                      onClick={() => toggleSection('ragContext')}
                      className="w-full flex items-center justify-between p-4 text-left hover:bg-slate-700/50 transition"
                    >
                      <span className="font-medium text-white">Documentation Context Used</span>
                      {expandedSections.ragContext ? (
                        <ChevronUp className="w-5 h-5 text-slate-400" />
                      ) : (
                        <ChevronDown className="w-5 h-5 text-slate-400" />
                      )}
                    </button>
                    {expandedSections.ragContext && (
                      <div className="px-4 pb-4 space-y-2">
                        {result.rag_context_used.map((ctx, i) => (
                          <div key={i} className="bg-slate-900 p-3 rounded-lg">
                            <pre className="text-xs text-slate-400 whitespace-pre-wrap font-mono">
                              {ctx.substring(0, 300)}...
                            </pre>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
