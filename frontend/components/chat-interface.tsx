'use client'

import * as React from 'react'
import { Send, Loader2, AlertCircle, FileText, ExternalLink } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { AgentTimeline } from '@/components/agent-timeline'
import { SourcePreview } from '@/components/source-preview'
import { useSearch } from '@/hooks/useSearch'
import { Source } from '@/types'
import { motion, AnimatePresence } from 'framer-motion'

export function ChatInterface() {
  const [query, setQuery] = React.useState('')
  const [selectedSource, setSelectedSource] = React.useState<Source | null>(null)
  const { search, reset, loading, error, result, agentStatuses } = useSearch()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim() || loading) return
    await search(query)
  }

  const handleNewSearch = () => {
    reset()
    setQuery('')
  }

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold">IKB Navigator</h1>
              <p className="text-sm text-muted-foreground">
                AI-Powered Knowledge Assistant
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto flex-1 overflow-auto px-4 py-8">
        <div className="mx-auto max-w-4xl space-y-6">
          {/* Search Input */}
          <Card>
            <CardContent className="pt-6">
              <form onSubmit={handleSubmit} className="flex gap-2">
                <Input
                  placeholder="Ask me anything about your documents..."
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  disabled={loading}
                  className="flex-1"
                />
                <Button type="submit" disabled={loading || !query.trim()}>
                  {loading ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Send className="h-4 w-4" />
                  )}
                </Button>
              </form>
            </CardContent>
          </Card>

          {/* Agent Timeline */}
          <AnimatePresence>
            {agentStatuses.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
              >
                <Card>
                  <CardContent className="pt-6">
                    <AgentTimeline agents={agentStatuses} />
                  </CardContent>
                </Card>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Error Message */}
          {error && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
            >
              <Card className="border-destructive">
                <CardContent className="flex items-center gap-3 pt-6">
                  <AlertCircle className="h-5 w-5 text-destructive" />
                  <p className="text-sm text-destructive">{error}</p>
                </CardContent>
              </Card>
            </motion.div>
          )}

          {/* Results */}
          {result && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-6"
            >
              {/* Answer */}
              <Card>
                <CardHeader>
                  <CardTitle>Answer</CardTitle>
                  <CardDescription>
                    Generated in {result.processing_time.toFixed(2)}s
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <p className="whitespace-pre-wrap text-foreground">
                    {result.answer}
                  </p>
                </CardContent>
              </Card>

              {/* Sources */}
              {result.sources.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle>Sources</CardTitle>
                    <CardDescription>
                      {result.sources.length} document{result.sources.length !== 1 ? 's' : ''} found
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    {/* Grouped Sources */}
                    {Object.keys(result.grouped_sources).length > 0 ? (
                      <div className="space-y-6">
                        {Object.entries(result.grouped_sources).map(
                          ([category, { count, documents }]) => (
                            <div key={category}>
                              <div className="mb-3 flex items-center gap-2">
                                <h4 className="text-sm font-semibold">{category}</h4>
                                <Badge variant="secondary">{count}</Badge>
                              </div>
                              <div className="space-y-2">
                                {documents.map((source, index) => (
                                  <div
                                    key={index}
                                    className="group flex items-start gap-3 rounded-lg border p-3 transition-colors hover:bg-accent cursor-pointer"
                                    onClick={() => setSelectedSource(source)}
                                  >
                                    <FileText className="mt-0.5 h-4 w-4 text-muted-foreground" />
                                    <div className="flex-1 space-y-1">
                                      <p className="text-sm font-medium leading-none">
                                        {source.title}
                                      </p>
                                      {source.snippet && (
                                        <p className="line-clamp-2 text-xs text-muted-foreground">
                                          {source.snippet}
                                        </p>
                                      )}
                                    </div>
                                    <Button
                                      variant="ghost"
                                      size="icon"
                                      className="h-8 w-8 opacity-0 group-hover:opacity-100"
                                      asChild
                                      onClick={(e) => e.stopPropagation()}
                                    >
                                      <a
                                        href={source.url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                      >
                                        <ExternalLink className="h-4 w-4" />
                                      </a>
                                    </Button>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )
                        )}
                      </div>
                    ) : (
                      // Ungrouped Sources
                      <div className="space-y-2">
                        {result.sources.map((source, index) => (
                          <div
                            key={index}
                            className="group flex items-start gap-3 rounded-lg border p-3 transition-colors hover:bg-accent cursor-pointer"
                            onClick={() => setSelectedSource(source)}
                          >
                            <FileText className="mt-0.5 h-4 w-4 text-muted-foreground" />
                            <div className="flex-1 space-y-1">
                              <p className="text-sm font-medium leading-none">
                                {source.title}
                              </p>
                              {source.snippet && (
                                <p className="line-clamp-2 text-xs text-muted-foreground">
                                  {source.snippet}
                                </p>
                              )}
                            </div>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-8 w-8 opacity-0 group-hover:opacity-100"
                              asChild
                              onClick={(e) => e.stopPropagation()}
                            >
                              <a
                                href={source.url}
                                target="_blank"
                                rel="noopener noreferrer"
                              >
                                <ExternalLink className="h-4 w-4" />
                              </a>
                            </Button>
                          </div>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              )}

              {/* New Search Button */}
              <div className="flex justify-center">
                <Button variant="outline" onClick={handleNewSearch}>
                  New Search
                </Button>
              </div>
            </motion.div>
          )}

          {/* Empty State */}
          {!loading && !result && !error && agentStatuses.length === 0 && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex flex-col items-center justify-center py-12 text-center"
            >
              <div className="rounded-full bg-primary/10 p-6">
                <FileText className="h-12 w-12 text-primary" />
              </div>
              <h2 className="mt-6 text-2xl font-semibold">
                Search Your Knowledge Base
              </h2>
              <p className="mt-2 max-w-md text-muted-foreground">
                Ask questions about your documents and get AI-powered answers with
                relevant sources from your Google Drive.
              </p>
            </motion.div>
          )}
        </div>
      </div>

      {/* Source Preview Modal */}
      <SourcePreview
        source={selectedSource}
        onClose={() => setSelectedSource(null)}
      />
    </div>
  )
}
