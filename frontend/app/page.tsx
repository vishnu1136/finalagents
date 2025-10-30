'use client'

import { ChatInterface } from '@/components/chat-interface'
import { ThemeToggle } from '@/components/theme-toggle'

export default function Home() {
  return (
    <div className="relative flex h-screen flex-col">
      {/* Theme Toggle - Fixed Position */}
      <div className="fixed right-4 top-4 z-50">
        <ThemeToggle />
      </div>

      {/* Main Chat Interface */}
      <ChatInterface />
    </div>
  )
}
