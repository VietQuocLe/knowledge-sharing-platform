import { useState } from 'react'
import { BookOpen, Search, Loader2 } from 'lucide-react'
import { useAuth } from '../features/auth'
import {
    useNotebooks,
    NotebookCard,
    CreateNotebookCard,
    CreateNotebookModal,
} from '../features/notebooks'
import { EmptyState } from '../components/ui/EmptyState'

export function MyNotebooksPage() {
    const { user } = useAuth()
    const { data: notebooks = [], isLoading } = useNotebooks()
    const [isModalOpen, setIsModalOpen] = useState(false)
    const [searchQuery, setSearchQuery] = useState('')

    const getGreeting = () => {
        const hour = new Date().getHours()
        if (hour >= 5 && hour < 12) return 'Chào buổi sáng'
        if (hour >= 12 && hour < 18) return 'Chào buổi chiều'
        return 'Chào buổi tối'
    }

    const filteredNotebooks = notebooks.filter((notebook) => {
        const query = searchQuery.toLowerCase().trim()
        return (
            notebook.title.toLowerCase().includes(query) ||
            (notebook.subject_name && notebook.subject_name.toLowerCase().includes(query))
        )
    })

    return (
        <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
            {/* Welcome Header */}
            <div className="mb-8">
                <h1 className="text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">
                    {getGreeting()}{user?.full_name ? `, ${user.full_name}` : ''}!
                </h1>
                <p className="mt-2 text-sm text-slate-500">
                    Chào mừng quay trở lại với Workspace của bạn. Hãy cùng quản lý các sổ ghi chú và tài liệu học tập của mình nhé.
                </p>
            </div>

            {/* Local Filter Subtitle & Search */}
            <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                <h2 className="text-lg font-semibold text-slate-800">Sổ ghi chú của tôi</h2>
                <div className="relative w-full max-w-xs">
                    <input
                        type="text"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        placeholder="Tìm kiếm sổ ghi chú nhanh..."
                        className="w-full rounded-xl border border-slate-200 bg-white py-2 pl-4 pr-10 text-xs text-slate-800 placeholder-slate-400 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 transition"
                    />
                    <Search className="absolute right-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-400" />
                </div>
            </div>

            {/* Loading State */}
            {isLoading ? (
                <div className="flex h-60 items-center justify-center">
                    <Loader2 className="h-8 w-8 animate-spin text-indigo-650" />
                </div>
            ) : (
                <>
                    {filteredNotebooks.length === 0 && searchQuery.trim() !== '' ? (
                        <div className="space-y-6">
                            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                                <CreateNotebookCard onClick={() => setIsModalOpen(true)} />
                            </div>
                            <EmptyState
                                title="Không tìm thấy kết quả"
                                description={`Không tìm thấy sổ ghi chú nào khớp với từ khóa "${searchQuery}"`}
                            />
                        </div>
                    ) : notebooks.length === 0 ? (
                        <EmptyState
                            icon={<BookOpen className="h-12 w-12 text-slate-400" />}
                            title="Chưa có sổ ghi chú nào"
                            description="Hãy bắt đầu tạo sổ ghi chú đầu tiên để lưu trữ tài liệu môn học và sử dụng AI trợ giúp."
                            action={{
                                label: 'Tạo sổ ghi chú mới',
                                onClick: () => setIsModalOpen(true),
                            }}
                        />
                    ) : (
                        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                            <CreateNotebookCard onClick={() => setIsModalOpen(true)} />
                            {filteredNotebooks.map((notebook) => (
                                <NotebookCard key={notebook.id} notebook={notebook} />
                            ))}
                        </div>
                    )}
                </>
            )}

            {/* Modal */}
            <CreateNotebookModal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} />
        </div>
    )
}
