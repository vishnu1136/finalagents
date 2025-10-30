'use client'

import * as React from 'react'
import { ExternalLink, FileText, X } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Source } from '@/types'
import { motion, AnimatePresence } from 'framer-motion'

interface SourcePreviewProps {
  source: Source | null
  onClose: () => void
}

export function SourcePreview({ source, onClose }: SourcePreviewProps) {
  if (!source) return null

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      >
        <motion.div
          initial={{ scale: 0.95, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.95, opacity: 0 }}
          className="fixed left-1/2 top-1/2 z-50 w-full max-w-2xl -translate-x-1/2 -translate-y-1/2"
          onClick={(e) => e.stopPropagation()}
        >
          <Card className="max-h-[80vh] overflow-hidden">
            <CardHeader className="flex flex-row items-start justify-between space-y-0">
              <div className="space-y-1 pr-8">
                <CardTitle className="flex items-center gap-2">
                  <FileText className="h-5 w-5" />
                  {source.title}
                </CardTitle>
                {source.type && (
                  <Badge variant="secondary" className="text-xs">
                    {source.type}
                  </Badge>
                )}
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={onClose}
                className="h-6 w-6 rounded-full"
              >
                <X className="h-4 w-4" />
              </Button>
            </CardHeader>
            <CardContent className="space-y-4">
              {source.snippet && (
                <div>
                  <h4 className="mb-2 text-sm font-semibold">Content Preview</h4>
                  <p className="text-sm text-muted-foreground">{source.snippet}</p>
                </div>
              )}

              <div className="flex items-center justify-between border-t pt-4">
                <div className="text-sm text-muted-foreground">
                  {source.score !== undefined && (
                    <span>Relevance: {(source.score * 100).toFixed(0)}%</span>
                  )}
                </div>
                <Button asChild>
                  <a
                    href={source.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2"
                  >
                    Open in Google Drive
                    <ExternalLink className="h-4 w-4" />
                  </a>
                </Button>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  )
}
