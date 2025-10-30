'use client'

import * as React from 'react'
import { motion } from 'framer-motion'
import { CheckCircle2, Circle, Loader2, XCircle, Clock } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Badge } from '@/components/ui/badge'
import { AgentStatus } from '@/types'

interface AgentTimelineProps {
  agents: AgentStatus[]
  className?: string
}

export function AgentTimeline({ agents, className }: AgentTimelineProps) {
  if (agents.length === 0) {
    return null
  }

  const getStatusIcon = (status: AgentStatus['status']) => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className="h-5 w-5 text-green-500" />
      case 'running':
        return <Loader2 className="h-5 w-5 text-blue-500 animate-spin" />
      case 'error':
        return <XCircle className="h-5 w-5 text-red-500" />
      case 'idle':
      default:
        return <Circle className="h-5 w-5 text-gray-400" />
    }
  }

  const getStatusColor = (status: AgentStatus['status']) => {
    switch (status) {
      case 'completed':
        return 'bg-green-500'
      case 'running':
        return 'bg-blue-500'
      case 'error':
        return 'bg-red-500'
      case 'idle':
      default:
        return 'bg-gray-400'
    }
  }

  const formatDuration = (duration?: number) => {
    if (!duration) return '...'
    return `${duration.toFixed(2)}s`
  }

  return (
    <div className={cn('w-full', className)}>
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-muted-foreground">
          Agent Pipeline
        </h3>
        <Badge variant="secondary" className="text-xs">
          {agents.filter((a) => a.status === 'completed').length} / {agents.length} Complete
        </Badge>
      </div>

      {/* Timeline View */}
      <div className="relative">
        {/* Progress Bar Background */}
        <div className="absolute left-0 top-6 h-0.5 w-full bg-gray-200 dark:bg-gray-800" />

        {/* Progress Bar Fill */}
        <motion.div
          className="absolute left-0 top-6 h-0.5 bg-blue-500"
          initial={{ width: '0%' }}
          animate={{
            width: `${(agents.filter((a) => a.status === 'completed').length / agents.length) * 100}%`,
          }}
          transition={{ duration: 0.5 }}
        />

        {/* Agent Steps */}
        <div className="relative flex justify-between">
          {agents.map((agent, index) => (
            <motion.div
              key={agent.name}
              className="flex flex-col items-center"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              {/* Icon */}
              <div
                className={cn(
                  'relative z-10 flex h-12 w-12 items-center justify-center rounded-full border-4 border-background',
                  agent.status === 'running' && 'ring-2 ring-blue-500 ring-offset-2',
                  agent.status === 'completed' && 'bg-green-50 dark:bg-green-950',
                  agent.status === 'error' && 'bg-red-50 dark:bg-red-950',
                  agent.status === 'idle' && 'bg-gray-50 dark:bg-gray-950'
                )}
              >
                {getStatusIcon(agent.status)}
              </div>

              {/* Agent Name */}
              <div className="mt-3 text-center">
                <p className={cn(
                  'text-xs font-medium',
                  agent.status === 'running' && 'text-blue-600 dark:text-blue-400',
                  agent.status === 'completed' && 'text-foreground',
                  agent.status === 'error' && 'text-red-600 dark:text-red-400',
                  agent.status === 'idle' && 'text-muted-foreground'
                )}>
                  {agent.name}
                </p>

                {/* Duration */}
                {agent.duration !== undefined && (
                  <div className="mt-1 flex items-center justify-center gap-1 text-xs text-muted-foreground">
                    <Clock className="h-3 w-3" />
                    <span>{formatDuration(agent.duration)}</span>
                  </div>
                )}

                {/* Status Message */}
                {agent.message && agent.status === 'running' && (
                  <p className="mt-1 max-w-[120px] truncate text-xs text-muted-foreground">
                    {agent.message}
                  </p>
                )}
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Detailed View (Optional - shows for running agent) */}
      {agents.some((a) => a.status === 'running') && (
        <motion.div
          className="mt-6 rounded-lg bg-blue-50 p-4 dark:bg-blue-950/20"
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          exit={{ opacity: 0, height: 0 }}
        >
          {agents
            .filter((a) => a.status === 'running')
            .map((agent) => (
              <div key={agent.name} className="flex items-center gap-3">
                <Loader2 className="h-4 w-4 animate-spin text-blue-500" />
                <div>
                  <p className="text-sm font-medium text-blue-900 dark:text-blue-100">
                    {agent.name} is working...
                  </p>
                  {agent.message && (
                    <p className="text-xs text-blue-700 dark:text-blue-300">
                      {agent.message}
                    </p>
                  )}
                </div>
              </div>
            ))}
        </motion.div>
      )}
    </div>
  )
}
