import { useState, useRef, useEffect, useCallback } from 'react'
import { fetchEventSource } from '@microsoft/fetch-event-source'

export interface Citation {
    index: number
    file_name: string
    page_number: number
    asset_id: number
}

export interface UseNotebookChatStreamResult {
    content: string
    isStreaming: boolean
    citations: Citation[]
    error: Error | null
    sendQuestion: (sessionId: number, questionContent: string) => Promise<void>
    abort: () => void
}

export function useNotebookChatStream(notebookId: number): UseNotebookChatStreamResult {
    const [content, setContent] = useState('')
    const [isStreaming, setIsStreaming] = useState(false)
    const [citations, setCitations] = useState<Citation[]>([])
    const [error, setError] = useState<Error | null>(null)

    const abortControllerRef = useRef<AbortController | null>(null)

    const abort = useCallback(() => {
        if (abortControllerRef.current) {
            abortControllerRef.current.abort()
            setIsStreaming(false)
        }
    }, [])

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            if (abortControllerRef.current) {
                abortControllerRef.current.abort()
            }
        }
    }, [])

    const sendQuestion = useCallback(async (sessionId: number, questionContent: string) => {
        // Abort previous stream if active
        if (abortControllerRef.current) {
            abortControllerRef.current.abort()
        }

        // Reset state before streaming
        setContent('')
        setCitations([])
        setError(null)
        setIsStreaming(true)

        const abortController = new AbortController()
        abortControllerRef.current = abortController

        const token = localStorage.getItem('access_token')
        const headers: Record<string, string> = {
            'Content-Type': 'application/json',
        }
        if (token) {
            headers['Authorization'] = `Bearer ${token}`
        }

        const baseUrl = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'
        const url = `${baseUrl}/notebooks/${notebookId}/sessions/${sessionId}/chat`

        try {
            await fetchEventSource(url, {
                method: 'POST',
                headers,
                body: JSON.stringify({ role: 'user', content: questionContent }),
                signal: abortController.signal,
                openWhenHidden: true,
                async onopen(response) {
                    if (response.ok && response.headers.get('content-type')?.includes('text/event-stream')) {
                        return // Expecting event stream
                    }
                    if (response.status >= 400 && response.status < 500 && response.status !== 429) {
                        const errData = await response.json().catch(() => ({}))
                        throw new Error(errData.detail || `Request failed with status ${response.status}`)
                    }
                    throw new Error(`Failed to open stream, status: ${response.status}`)
                },
                onmessage(ev) {
                    const eventType = ev.event
                    const data = ev.data

                    switch (eventType) {
                        case 'citations': {
                            try {
                                const parsedCitations = JSON.parse(data) as Citation[]
                                setCitations(parsedCitations)
                            } catch (e) {
                                console.error('Failed to parse citations event:', e)
                            }
                            break
                        }
                        case 'delta': {
                            try {
                                const parsedDelta = JSON.parse(data) as string
                                setContent((prev) => prev + parsedDelta)
                            } catch (e) {
                                console.error('Failed to parse delta event:', e)
                            }
                            break
                        }
                        case 'done': {
                            setIsStreaming(false)
                            break
                        }
                        case 'error': {
                            try {
                                const parsedError = JSON.parse(data) as { message: string }
                                setError(new Error(parsedError.message || 'Error occurred during streaming'))
                            } catch (e) {
                                setError(new Error(data || 'Error occurred during streaming'))
                            }
                            setIsStreaming(false)
                            if (abortControllerRef.current) {
                                abortControllerRef.current.abort()
                            }
                            break
                        }
                        default:
                            break
                    }
                },
                onerror(err) {
                    // Always rethrow to disable the auto-retry behavior of the library
                    setError(err instanceof Error ? err : new Error(String(err)))
                    setIsStreaming(false)
                    throw err
                }
            })
        } catch (err: any) {
            if (err.name === 'AbortError') {
                // Keeping output up to abort point, do not set error state
                return
            }
            setError(err instanceof Error ? err : new Error(String(err)))
            setIsStreaming(false)
        }
    }, [notebookId])

    return {
        content,
        isStreaming,
        citations,
        error,
        sendQuestion,
        abort
    }
}
