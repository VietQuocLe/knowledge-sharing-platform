import { useState, useEffect, useRef } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Sparkles, Send, Square, Bot, Plus, X, Loader2, Check, Copy } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkMath from 'remark-math'
import rehypeKatex from 'rehype-katex'
import { notebooksApi, useNotebookChatStream } from '../index'
import { toast } from 'react-hot-toast'
import { ErrorMessage } from '../../../components/ui/ErrorMessage'
import { ChatSessionHistoryPopover } from './ChatSessionHistoryPopover'
import { PdfPreviewModal } from '../../documents'

interface CodeBlockProps {
    className?: string
    children: React.ReactNode
}

function CodeBlock({ className, children }: CodeBlockProps) {
    const [copied, setCopied] = useState(false)
    const rawCode = String(children).replace(/\n$/, '')

    const handleCopy = async () => {
        try {
            await navigator.clipboard.writeText(rawCode)
            setCopied(true)
            setTimeout(() => setCopied(false), 2000)
        } catch (err) {
            console.error('Failed to copy code: ', err)
        }
    }

    return (
        <div className="relative my-3 rounded-xl border border-slate-200 bg-slate-900 overflow-hidden text-slate-200 font-mono text-xs">
            <div className="flex items-center justify-between px-4 py-2 border-b border-slate-800 bg-slate-950/80 text-[10px] text-slate-400 font-sans tracking-wide">
                <span>CODE</span>
                <button
                    type="button"
                    onClick={handleCopy}
                    className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 hover:text-white transition active:scale-95 cursor-pointer"
                >
                    {copied ? (
                        <>
                            <Check className="h-3 w-3 text-green-400" />
                            <span className="text-green-400">Đã chép</span>
                        </>
                    ) : (
                        <>
                            <Copy className="h-3 w-3" />
                            <span>Sao chép</span>
                        </>
                    )}
                </button>
            </div>
            <pre className="p-4 overflow-x-auto leading-relaxed text-slate-100">
                <code className={className}>{children}</code>
            </pre>
        </div>
    )
}

interface NotebookChatPanelProps {
    notebookId: number
    onClose: () => void
}

export function NotebookChatPanel({ notebookId, onClose }: NotebookChatPanelProps) {
    const [searchParams, setSearchParams] = useSearchParams()
    const queryClient = useQueryClient()
    const [chatInput, setChatInput] = useState('')
    const [userMessage, setUserMessage] = useState('')

    // Preview state for credentials/citations
    const [previewState, setPreviewState] = useState<{
        isOpen: boolean
        fileUrl: string | null
        fileName: string
        isLoadingUrl: boolean
        pageNumber?: number
    }>({
        isOpen: false,
        fileUrl: null,
        fileName: '',
        isLoadingUrl: false,
    })

    const handleOpenCitation = async (citation: any) => {
        setPreviewState({
            isOpen: true,
            fileUrl: null,
            fileName: citation.file_name,
            isLoadingUrl: true,
            pageNumber: citation.page_number
        })
        try {
            const res = await notebooksApi.downloadAsset(notebookId, citation.asset_id)
            setPreviewState({
                isOpen: true,
                fileUrl: res.download_url,
                fileName: citation.file_name,
                isLoadingUrl: false,
                pageNumber: citation.page_number
            })
        } catch (err: any) {
            toast.error('Không thể tải tập tin xem trước.')
            setPreviewState({
                isOpen: false,
                fileUrl: null,
                fileName: '',
                isLoadingUrl: false
            })
        }
    }

    const preprocessContent = (text: string) => {
        return text.replace(/\[(\d+)\]/g, '[$1](citation:$1)')
    }

    const injectCursor = (children: React.ReactNode, messageId: number): React.ReactNode => {
        if (!isStreaming || messageId !== -2) return children

        if (typeof children === 'string') {
            if (children.endsWith(' █')) {
                return (
                    <>
                        {children.slice(0, -2)}
                        <span className="inline-block w-1.5 h-3.5 bg-indigo-600 animate-pulse ml-0.5 align-middle rounded-xs" />
                    </>
                )
            }
            return children
        }

        if (Array.isArray(children)) {
            const result = [...children]
            const lastIdx = result.length - 1
            if (lastIdx >= 0) {
                result[lastIdx] = injectCursor(result[lastIdx], messageId)
            }
            return result
        }

        return children
    }

    const activeSessionParam = searchParams.get('session')
    const activeSessionId = activeSessionParam ? Number(activeSessionParam) : null

    // Fetch session messages
    const {
        data: messages = [],
        isLoading: isLoadingMessages,
        error: loadMessagesError,
    } = useQuery({
        queryKey: ['notebooks', notebookId, 'sessions', activeSessionId, 'messages'],
        queryFn: () => {
            if (activeSessionId) {
                return notebooksApi.getSessionMessages(notebookId, activeSessionId)
            }
            return Promise.resolve([])
        },
        enabled: activeSessionId !== null && !isNaN(activeSessionId)
    })

    // Fetch overall session list to determine active title
    const { data: sessions = [] } = useQuery({
        queryKey: ['notebooks', notebookId, 'sessions'],
        queryFn: () => notebooksApi.listSessions(notebookId),
        enabled: !isNaN(notebookId) && notebookId > 0
    })

    // Hook to handle SSE stream
    const {
        content: streamContent,
        isStreaming,
        citations,
        error: streamError,
        sendQuestion,
        abort
    } = useNotebookChatStream(notebookId)

    const prevIsStreaming = useRef(false)
    const initialCountRef = useRef<number>(-1)
    const messagesEndRef = useRef<HTMLDivElement>(null)
    const textareaRef = useRef<HTMLTextAreaElement>(null)

    // Auto-expanding textarea height on chatInput changes
    useEffect(() => {
        const textarea = textareaRef.current
        if (textarea) {
            textarea.style.height = 'auto'
            textarea.style.height = `${Math.min(textarea.scrollHeight, 120)}px`
        }
    }, [chatInput])

    // Track previous sessionId to detect transitions and abort if switching/deleting active session
    const prevSessionIdRef = useRef<number | null>(activeSessionId)

    useEffect(() => {
        const prevSessionId = prevSessionIdRef.current
        prevSessionIdRef.current = activeSessionId

        // If the session ID changed from a non-null active session, abort the stream
        if (prevSessionId !== null && prevSessionId !== activeSessionId) {
            abort()
        }
    }, [activeSessionId, abort])

    // Reset initial count on session change
    useEffect(() => {
        initialCountRef.current = -1
        setUserMessage('')
    }, [activeSessionId])

    // Detect when stream ends to invalidate queries
    useEffect(() => {
        if (prevIsStreaming.current && !isStreaming) {
            if (streamError) {
                initialCountRef.current = -1
            } else if (activeSessionId) {
                queryClient.invalidateQueries({
                    queryKey: ['notebooks', notebookId, 'sessions', activeSessionId, 'messages']
                })
                queryClient.invalidateQueries({
                    queryKey: ['notebooks', notebookId, 'sessions']
                })
                setUserMessage('')
            }
        }
        prevIsStreaming.current = isStreaming
    }, [isStreaming, streamError, notebookId, activeSessionId, queryClient])

    // Determine if we should display virtual bubbles while waiting for Query refetch
    const isWaitingForFetch = initialCountRef.current >= 0 && messages.length <= initialCountRef.current

    // Construct local display message array during stream
    const pendingUserMsg = (isStreaming || isWaitingForFetch) && userMessage ? {
        id: -1,
        session_id: activeSessionId || 0,
        role: 'user' as const,
        content: userMessage,
        created_at: new Date().toISOString()
    } : null

    const pendingAssMsg = (isStreaming || isWaitingForFetch) && (streamContent || isStreaming) ? {
        id: -2,
        session_id: activeSessionId || 0,
        role: 'assistant' as const,
        content: streamContent,
        citations: citations,
        created_at: new Date().toISOString()
    } : null

    const displayMessages = [
        ...messages,
        ...(pendingUserMsg ? [pendingUserMsg] : []),
        ...(pendingAssMsg ? [pendingAssMsg] : [])
    ]

    // Title retrieval
    const activeSession = sessions.find(s => s.id === activeSessionId)
    const activeSessionTitle = activeSession ? activeSession.title : 'Đoạn chat mới'

    // Suggestions list
    const suggestions = [
        "💡 Tóm tắt nội dung tài liệu đã lưu",
        "❓ Giải thích các khái niệm cốt lõi trong tài liệu",
        "📝 Đề xuất các câu hỏi ôn tập dựa trên bài học"
    ]

    // Auto-scroll logic
    useEffect(() => {
        if (displayMessages.length > 0) {
            messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
        }
    }, [displayMessages, streamContent])

    // Send logic
    const handleSend = async (contentToSend: string) => {
        if (isStreaming || !contentToSend.trim()) return

        let sessionIdToUse = activeSessionId
        setUserMessage(contentToSend)
        setChatInput('')
        initialCountRef.current = messages.length

        try {
            // Lazy creations
            if (!sessionIdToUse) {
                initialCountRef.current = 0
                const newSession = await notebooksApi.createSession(notebookId, `Phiên trò chuyện mới`)
                sessionIdToUse = newSession.id

                // Update URL search parameter
                const nextParams = new URLSearchParams(searchParams)
                nextParams.set('session', String(newSession.id))
                setSearchParams(nextParams)

                // Prefetch list
                queryClient.invalidateQueries({
                    queryKey: ['notebooks', notebookId, 'sessions']
                })
            }

            // Stream question
            await sendQuestion(sessionIdToUse, contentToSend)
        } catch (err: any) {
            toast.error(err.message || 'Lỗi gửi tin nhắn')
            setUserMessage('')
            initialCountRef.current = -1
        }
    }

    const handleNewChat = () => {
        if (isStreaming) {
            abort()
        }
        setUserMessage('')
        const nextParams = new URLSearchParams(searchParams)
        nextParams.delete('session')
        setSearchParams(nextParams)
    }

    return (
        <div className="w-[360px] md:w-[400px] border-l border-slate-200 bg-slate-50/50 flex flex-col h-full shrink-0 shadow-3xs animate-in slide-in-from-right duration-250 font-sans">
            {/* Header Panel */}
            <div className="bg-white border-b border-slate-100 px-5 py-4 flex items-center justify-between">
                <div className="flex items-center gap-2 max-w-[60%]">
                    <div className="p-1.5 rounded-lg bg-indigo-50 text-indigo-600 shrink-0">
                        <Sparkles className="h-4 w-4" />
                    </div>
                    <div className="min-w-0">
                        <h3 className="text-xs font-bold text-slate-900 leading-snug truncate" title={activeSessionTitle}>
                            {activeSessionTitle}
                        </h3>
                    </div>
                </div>

                <div className="flex items-center gap-1.5 shrink-0">
                    <ChatSessionHistoryPopover notebookId={notebookId} />
                    <button
                        type="button"
                        onClick={handleNewChat}
                        className="p-1.5 rounded-xl text-slate-450 hover:bg-slate-100 hover:text-slate-700 transition"
                        title="Đoạn chat mới"
                    >
                        <Plus className="h-4 w-4" />
                    </button>
                    <button
                        type="button"
                        onClick={onClose}
                        className="p-1.5 rounded-xl text-slate-450 hover:bg-slate-100 hover:text-slate-700 transition"
                        title="Thu nhỏ khung AI"
                    >
                        <X className="h-4 w-4" />
                    </button>
                </div>
            </div>

            {/* Content view */}
            <div className="flex-1 overflow-y-auto p-5 flex flex-col gap-4">
                {activeSessionId === null ? (
                    /* Draft Screen Panel */
                    <div className="flex-1 flex flex-col items-center justify-center text-center p-4">
                        <div className="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-indigo-50 text-indigo-600 mb-4 animate-pulse">
                            <Bot className="h-6 w-6" />
                        </div>
                        <h4 className="text-sm font-bold text-slate-800 mb-1">Hỏi đáp tài liệu thông minh</h4>
                        <p className="text-xs text-slate-500 max-w-[260px] leading-relaxed mb-6">
                            Chào mừng bạn đến với AI Workspace. Hãy đặt câu hỏi bất kỳ về tài liệu đã lưu trong sổ tay này.
                        </p>

                        <div className="w-full text-left space-y-2 border-t border-slate-100 pt-4">
                            <p className="text-[10px] uppercase font-bold text-slate-400 tracking-wider mb-2.5">Đề xuất câu hỏi</p>
                            {suggestions.map((s, idx) => (
                                <button
                                    key={idx}
                                    type="button"
                                    onClick={() => handleSend(s)}
                                    className="w-full text-left p-3.5 text-xs text-slate-650 rounded-2xl bg-white border border-slate-200/80 hover:border-indigo-250 hover:bg-indigo-50/30 hover:shadow-xs transition duration-200 leading-snug cursor-pointer active:scale-[0.99]"
                                >
                                    {s}
                                </button>
                            ))}
                        </div>
                    </div>
                ) : (
                    /* Active Chat Screen */
                    <div className="flex-1 flex flex-col gap-4 min-h-0">
                        {loadMessagesError && (
                            <ErrorMessage message="Không thể tải lịch sử tin nhắn của phiên." />
                        )}

                        {isLoadingMessages ? (
                            <div className="flex-1 flex items-center justify-center">
                                <Loader2 className="h-6 w-6 text-indigo-600 animate-spin" />
                            </div>
                        ) : (
                            <div className="flex-1 overflow-y-auto pr-1 flex flex-col gap-3.5">
                                {displayMessages.length === 0 ? (
                                    <div className="text-center text-xs text-slate-400 italic py-10">
                                        Không có tin nhắn nào trong phiên này.
                                    </div>
                                ) : (
                                    displayMessages.map((m) => {
                                        const isUser = m.role === 'user'
                                        const msgCitations = isUser ? [] : (m.id === -2 ? citations : (m.citations || []))
                                        return (
                                            <div
                                                key={m.id}
                                                className={isUser
                                                    ? "self-end bg-indigo-600 text-white rounded-2xl rounded-tr-xs px-3.5 py-2.5 shadow-sm text-xs leading-relaxed max-w-[85%] break-words whitespace-pre-wrap"
                                                    : "self-start bg-white border border-slate-200/80 text-slate-850 rounded-2xl rounded-tl-xs p-3.5 shadow-xs text-xs leading-relaxed max-w-[85%]"
                                                }
                                            >
                                                {isUser ? (
                                                    <span>{m.content}</span>
                                                ) : !m.content ? (
                                                    <div className="flex items-center gap-2 text-slate-400 py-1">
                                                        <div className="flex gap-1 shrink-0">
                                                            <span className="h-1.5 w-1.5 rounded-full bg-indigo-500 animate-bounce [animation-delay:-0.3s]"></span>
                                                            <span className="h-1.5 w-1.5 rounded-full bg-indigo-500 animate-bounce [animation-delay:-0.15s]"></span>
                                                            <span className="h-1.5 w-1.5 rounded-full bg-indigo-500 animate-bounce"></span>
                                                        </div>
                                                        <span className="text-[11px] italic font-medium text-slate-500">Đang tìm tài liệu & suy nghĩ...</span>
                                                    </div>
                                                ) : (
                                                    <ReactMarkdown
                                                        urlTransform={(url) => url}
                                                        remarkPlugins={[remarkMath]}
                                                        rehypePlugins={[[rehypeKatex, { strict: false, throwOnError: false }]]}
                                                        components={{
                                                            code(props) {
                                                                const { children, className } = props
                                                                const hasNewline = String(children).includes('\n')
                                                                if (!hasNewline && !className) {
                                                                    return (
                                                                        <code className="bg-slate-100 text-indigo-600 px-1.5 py-0.5 rounded text-[10.5px] font-semibold break-words">
                                                                            {children}
                                                                        </code>
                                                                    )
                                                                }
                                                                return (
                                                                    <CodeBlock className={className}>
                                                                        {children}
                                                                    </CodeBlock>
                                                                )
                                                            },
                                                            h1: ({ children }) => <h1 className="text-sm font-bold text-slate-900 mt-3 mb-1.5">{injectCursor(children, m.id)}</h1>,
                                                            h2: ({ children }) => <h2 className="text-xs font-bold text-slate-900 mt-2.5 mb-1">{injectCursor(children, m.id)}</h2>,
                                                            h3: ({ children }) => <h3 className="text-xs font-bold text-slate-800 mt-2 mb-1">{injectCursor(children, m.id)}</h3>,
                                                            p: ({ children }) => <p className="mb-2 leading-relaxed text-xs break-words">{injectCursor(children, m.id)}</p>,
                                                            ul: ({ children }) => <ul className="list-disc pl-5 mb-2 space-y-1">{children}</ul>,
                                                            ol: ({ children }) => <ol className="list-decimal pl-5 mb-2 space-y-1">{children}</ol>,
                                                            li: ({ children }) => <li className="text-xs leading-relaxed">{injectCursor(children, m.id)}</li>,
                                                            table: ({ children }) => (
                                                                <div className="overflow-x-auto my-3 border border-slate-200 rounded-xl">
                                                                    <table className="min-w-full divide-y divide-slate-200 text-xs text-left">
                                                                        {children}
                                                                    </table>
                                                                </div>
                                                            ),
                                                            thead: ({ children }) => <thead className="bg-slate-50">{children}</thead>,
                                                            tbody: ({ children }) => <tbody className="divide-y divide-slate-100 bg-white">{children}</tbody>,
                                                            tr: ({ children }) => <tr>{children}</tr>,
                                                            th: ({ children }) => <th className="px-3 py-2 font-semibold text-slate-700 text-[11px] uppercase tracking-wider">{children}</th>,
                                                            td: ({ children }) => <td className="px-3 py-2 text-slate-650">{injectCursor(children, m.id)}</td>,
                                                            a(props) {
                                                                const { children, href } = props
                                                                if (href && href.startsWith('citation:')) {
                                                                    const indexStr = href.replace('citation:', '')
                                                                    const citationIndex = parseInt(indexStr, 10)
                                                                    const citation = msgCitations.find(c => c.index === citationIndex)

                                                                    // Fallback: if not found in list, render as raw text [X]
                                                                    if (!citation) {
                                                                        return <span>[{indexStr}]</span>
                                                                    }

                                                                    return (
                                                                        <button
                                                                            type="button"
                                                                            onClick={() => handleOpenCitation(citation)}
                                                                            className="inline-flex items-center justify-center px-1.5 py-0.5 mx-0.5 text-[10px] font-bold rounded-md bg-indigo-50 hover:bg-indigo-100 text-indigo-600 hover:text-indigo-700 border border-indigo-200 transition cursor-pointer active:scale-95 whitespace-nowrap"
                                                                        >
                                                                            [{citationIndex}]
                                                                        </button>
                                                                    )
                                                                }
                                                                return (
                                                                    <a href={href} target="_blank" rel="noopener noreferrer" className="text-indigo-600 hover:underline">
                                                                        {children}
                                                                    </a>
                                                                )
                                                            }
                                                        }}
                                                    >
                                                        {preprocessContent(m.content) + (m.id === -2 && isStreaming && m.content ? ' █' : '')}
                                                    </ReactMarkdown>
                                                )}

                                                {/* Citations block (if any) */}
                                                {!isUser && m.citations && m.citations.length > 0 && (
                                                    <div className="mt-2 pt-2 border-t border-slate-100 flex flex-wrap gap-1.5">
                                                        {m.citations.map((c: any) => (
                                                            <button
                                                                key={c.index}
                                                                type="button"
                                                                onClick={() => handleOpenCitation(c)}
                                                                className="text-[9px] font-semibold text-indigo-600 bg-indigo-50 hover:bg-indigo-100 hover:border-indigo-200 transition px-2 py-0.5 rounded border border-indigo-100 cursor-pointer flex items-center gap-1 active:scale-95"
                                                            >
                                                                [{c.index}] {c.file_name} (Trang {c.page_number})
                                                            </button>
                                                        ))}
                                                    </div>
                                                )}
                                            </div>
                                        )
                                    })
                                )}
                                <div ref={messagesEndRef} />
                            </div>
                        )}

                        {streamError && (
                            <ErrorMessage message={`Lỗi phát trực tiếp: ${streamError.message}`} />
                        )}
                    </div>
                )}
            </div>

            {/* Input area */}
            <form
                onSubmit={(e) => {
                    e.preventDefault()
                    handleSend(chatInput)
                }}
                className="p-4 bg-white border-t border-slate-100"
            >
                <div className="flex items-end gap-2 rounded-2xl border border-slate-200 bg-slate-50/50 px-3 py-2">
                    <textarea
                        ref={textareaRef}
                        rows={1}
                        value={chatInput}
                        onChange={(e) => setChatInput(e.target.value)}
                        onKeyDown={(e) => {
                            if (e.key === 'Enter' && !e.shiftKey) {
                                e.preventDefault()
                                if (chatInput.trim() && !isStreaming) {
                                    handleSend(chatInput)
                                }
                            }
                        }}
                        disabled={isStreaming}
                        placeholder={isStreaming ? "Đang chờ AI trả lời..." : "Hỏi đáp về tài liệu..."}
                        className="flex-1 bg-transparent text-xs focus:outline-none text-slate-700 placeholder-slate-400 disabled:cursor-not-allowed resize-none max-h-[120px] py-1.5 leading-relaxed min-h-[36px]"
                        style={{ height: '36px' }}
                    />

                    {isStreaming ? (
                        <button
                            type="button"
                            onClick={abort}
                            className="p-1.5 rounded-xl bg-rose-50 text-rose-600 hover:bg-rose-100 transition shadow-3xs cursor-pointer flex items-center justify-center mb-1 shrink-0"
                            title="Dừng phản hồi"
                        >
                            <Square className="h-3.5 w-3.5 fill-rose-600" />
                        </button>
                    ) : (
                        <button
                            type="submit"
                            disabled={isStreaming || !chatInput.trim()}
                            className="p-1.5 rounded-xl bg-indigo-600 text-white hover:bg-indigo-700 disabled:bg-slate-100 disabled:text-slate-400 disabled:cursor-not-allowed transition shadow-3xs cursor-pointer flex items-center justify-center mb-1 shrink-0"
                            title="Gửi"
                        >
                            <Send className="h-3.5 w-3.5" />
                        </button>
                    )}
                </div>
            </form>

            <PdfPreviewModal
                isOpen={previewState.isOpen}
                onClose={() => setPreviewState(prev => ({ ...prev, isOpen: false }))}
                fileUrl={previewState.fileUrl}
                fileName={previewState.fileName}
                isLoadingUrl={previewState.isLoadingUrl}
                pageNumber={previewState.pageNumber}
            />
        </div>
    )
}
