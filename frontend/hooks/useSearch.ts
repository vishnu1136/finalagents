'use client'

import { useState } from 'react'
import { api, APIError } from '@/lib/api'
import { SearchResponse, AgentStatus } from '@/types'

export function useSearch() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<SearchResponse | null>(null)
  const [agentStatuses, setAgentStatuses] = useState<AgentStatus[]>([])

  const search = async (query: string) => {
    if (!query.trim()) {
      setError('Please enter a search query')
      return
    }

    setLoading(true)
    setError(null)
    setResult(null)

    // Initialize agent statuses for the pipeline
    const initialAgents: AgentStatus[] = [
      { name: 'Query Understanding', status: 'idle' },
      { name: 'Search', status: 'idle' },
      { name: 'Analysis', status: 'idle' },
      { name: 'Answer Generation', status: 'idle' },
    ]
    setAgentStatuses(initialAgents)

    try {
      // Simulate agent progression (since we don't have real-time updates from backend)
      // In production, you could use WebSockets or Server-Sent Events

      // Query Understanding Agent
      setAgentStatuses((prev) =>
        prev.map((agent, i) =>
          i === 0
            ? { ...agent, status: 'running', startTime: Date.now(), message: 'Understanding your query...' }
            : agent
        )
      )

      await new Promise((resolve) => setTimeout(resolve, 500))

      setAgentStatuses((prev) =>
        prev.map((agent, i) =>
          i === 0
            ? { ...agent, status: 'completed', endTime: Date.now(), duration: 0.5 }
            : i === 1
            ? { ...agent, status: 'running', startTime: Date.now(), message: 'Searching Google Drive...' }
            : agent
        )
      )

      await new Promise((resolve) => setTimeout(resolve, 1000))

      // Search Agent
      setAgentStatuses((prev) =>
        prev.map((agent, i) =>
          i === 1
            ? { ...agent, status: 'completed', endTime: Date.now(), duration: 1.0 }
            : i === 2
            ? { ...agent, status: 'running', startTime: Date.now(), message: 'Analyzing results...' }
            : agent
        )
      )

      await new Promise((resolve) => setTimeout(resolve, 500))

      // Analysis Agent
      setAgentStatuses((prev) =>
        prev.map((agent, i) =>
          i === 2
            ? { ...agent, status: 'completed', endTime: Date.now(), duration: 0.5 }
            : i === 3
            ? { ...agent, status: 'running', startTime: Date.now(), message: 'Generating response...' }
            : agent
        )
      )

      // Make the actual API call
      const response = await api.search(query)

      // Update agent times from response
      if (response.agent_times) {
        setAgentStatuses((prev) =>
          prev.map((agent) => {
            const agentKey = agent.name.toLowerCase().replace(/ /g, '_')
            if (response.agent_times[agentKey]) {
              return { ...agent, duration: response.agent_times[agentKey] }
            }
            return agent
          })
        )
      }

      // Answer Generation Agent complete
      setAgentStatuses((prev) =>
        prev.map((agent, i) =>
          i === 3 ? { ...agent, status: 'completed', endTime: Date.now() } : agent
        )
      )

      setResult(response)
    } catch (err) {
      const errorMessage =
        err instanceof APIError
          ? `Search failed: ${err.message}`
          : 'An unexpected error occurred'

      setError(errorMessage)

      // Mark current running agent as error
      setAgentStatuses((prev) =>
        prev.map((agent) =>
          agent.status === 'running' ? { ...agent, status: 'error' } : agent
        )
      )
    } finally {
      setLoading(false)
    }
  }

  const reset = () => {
    setResult(null)
    setError(null)
    setAgentStatuses([])
  }

  return {
    search,
    reset,
    loading,
    error,
    result,
    agentStatuses,
  }
}
