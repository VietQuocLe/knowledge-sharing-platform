import { useState } from 'react'
import { History, Search, Edit2, Trash2, X, Loader2 } from 'lucide-react'
import { useSearchParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { notebooksApi } from '../api'
import { useClickOutside } from '../../../hooks/useClickOutside'
import { RenameSessionModal } from './RenameSessionModal'
import { DeleteSessionConfirmModal } from './DeleteSessionConfirmModal'

interface ChatSessionHistoryPopoverProps {
    notebookId: number
}

export function ChatSessionHistoryPopover({ notebookId }: ChatSessionHistoryPopoverProps) {
    const [isOpen, setIsOpen] = useState(false)
    const [searchParams, setSearchParams] = useSearchParams()
    const [searchQuery, setSearchQuery] = useState('')

    // Modals state
    const [selectedSessionForRename, setSelectedSessionForRename] = useState<{ id: number; title: string } | null>(null)
    const [selectedSessionForDelete, setSelectedSessionForDelete] = useState<{ id: number; title: string } | null>(null)

    // Load sessions list
    const { data: sessions = [], isLoading } = useQuery({
        queryKey: ['notebooks', notebookId, 'sessions'],
        queryFn: () => notebooksApi.listSessions(notebookId),
        enabled: isOpen,
    })

    const popoverRef = useClickOutside<HTMLDivElement>(() => setIsOpen(false))

    const activeSessionId = searchParams.get('session') ? Number(searchParams.get('session')) : null

    const handleSelectSession = (id: number) => {
        const nextParams = new URLSearchParams(searchParams)
        nextParams.set('session', String(id))
        setSearchParams(nextParams)
        setIsOpen(false)
    }

    const filteredSessions = sessions.filter(s =>
        s.title.toLowerCase().includes(searchQuery.toLowerCase())
    )

    return (
        <div className="relative" ref={popoverRef}>
            <button
                type="button"
                onClick={() => setIsOpen(!isOpen)}
                className={`p-1.5 rounded-xl transition ${isOpen ? 'bg-sky-50 text-sky-600' : 'text-slate-450 hover:bg-slate-100 hover:text-slate-700'}`}
                title="Lịch sử trò chuyện"
            >
                <History className="h-4 w-4" />
            </button>

            {isOpen && (
                <div className="absolute right-0 mt-2 w-72 md:w-80 rounded-2xl border border-slate-200 bg-white p-4 shadow-xl z-20 animate-in fade-in slide-in-from-top-2 duration-200">
                    <div className="flex items-center justify-between border-b border-slate-100 pb-3 mb-3">
                        <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider">Lịch sử trò chuyện</h4>
                        <button
                            type="button"
                            onClick={() => setIsOpen(false)}
                            className="p-1 rounded-lg text-slate-400 hover:bg-slate-50 hover:text-slate-650 transition"
                        >
                            <X className="h-3.5 w-3.5" />
                        </button>
                    </div>

                    {/* Search bar */}
                    <div className="relative mb-3.5">
                        <Search className="absolute left-3 top-2.5 h-3.5 w-3.5 text-slate-400" />
                        <input
                            type="text"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            placeholder="Tìm kiếm phiên trò chuyện..."
                            className="w-full pl-9 pr-4 py-1.5 text-xs rounded-xl border border-slate-200 placeholder-slate-400 focus:outline-none focus:border-sky-500 transition"
                        />
                    </div>

                    {/* Sessions list */}
                    <div className="max-h-60 overflow-y-auto space-y-1 pr-1 font-sans">
                        {isLoading ? (
                            <div className="py-8 flex items-center justify-center">
                                <Loader2 className="h-4 w-4 text-sky-600 animate-spin" />
                            </div>
                        ) : filteredSessions.length === 0 ? (
                            <div className="py-8 text-center text-xs text-slate-400 italic">
                                {searchQuery ? 'Không tìm thấy phiên trò chuyện' : 'Chưa có phiên trò chuyện nào'}
                            </div>
                        ) : (
                            filteredSessions.map((s) => {
                                const isActive = activeSessionId === s.id
                                return (
                                    <div
                                        key={s.id}
                                        className={`group flex items-center justify-between gap-1.5 p-2 rounded-xl transition ${isActive ? 'bg-sky-50/70 border border-sky-100/50 shadow-3xs' : 'hover:bg-slate-50 border border-transparent'}`}
                                    >
                                        <button
                                            type="button"
                                            onClick={() => handleSelectSession(s.id)}
                                            className={`flex-1 text-left text-xs truncate font-medium ${isActive ? 'text-slate-900 font-bold' : 'text-slate-700 hover:text-slate-900'}`}
                                            title={s.title}
                                        >
                                            {s.title}
                                        </button>

                                        <div className="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition shrink-0">
                                            <button
                                                type="button"
                                                onClick={(e) => {
                                                    e.stopPropagation()
                                                    setSelectedSessionForRename(s)
                                                }}
                                                className="p-1 rounded text-slate-400 hover:bg-white hover:text-sky-600 hover:shadow-3xs transition border border-transparent hover:border-slate-100"
                                                title="Đổi tên"
                                            >
                                                <Edit2 className="h-3 w-3" />
                                            </button>
                                            <button
                                                type="button"
                                                onClick={(e) => {
                                                    e.stopPropagation()
                                                    setSelectedSessionForDelete(s)
                                                }}
                                                className="p-1 rounded text-slate-400 hover:bg-white hover:text-rose-600 hover:shadow-3xs transition border border-transparent hover:border-slate-100"
                                                title="Xóa"
                                            >
                                                <Trash2 className="h-3 w-3" />
                                            </button>
                                        </div>
                                    </div>
                                )
                            })
                        )}
                    </div>
                </div>
            )}

            {selectedSessionForRename && (
                <RenameSessionModal
                    isOpen={true}
                    notebookId={notebookId}
                    session={selectedSessionForRename}
                    onClose={() => setSelectedSessionForRename(null)}
                />
            )}

            {selectedSessionForDelete && (
                <DeleteSessionConfirmModal
                    isOpen={true}
                    notebookId={notebookId}
                    session={selectedSessionForDelete}
                    onClose={() => setSelectedSessionForDelete(null)}
                />
            )}
        </div>
    )
}
