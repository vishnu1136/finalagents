export interface SearchRequest {
  query: string
  config?: Record<string, any>
}

export interface Source {
  title: string
  url: string
  snippet?: string
  type?: string
  chunk_id?: string
  score?: number
}

export interface GroupedSources {
  [category: string]: {
    count: number
    documents: Source[]
  }
}

export interface SearchResponse {
  answer: string
  sources: Source[]
  grouped_sources: GroupedSources
  processing_time: number
  request_id: string
  agent_times: Record<string, number>
  errors: string[]
}

export interface AgentStatus {
  name: string
  status: 'idle' | 'running' | 'completed' | 'error'
  startTime?: number
  endTime?: number
  duration?: number
  message?: string
}

export interface HealthResponse {
  status: string
  langgraph_a2a_running: boolean
  agent_count: number
  agent_status: Record<string, any>
  active_requests: number
  memory_checkpoints: number
  timestamp: string
}
