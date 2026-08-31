import { lazy, Suspense, type ComponentType } from 'react'
import { createBrowserRouter, RouterProvider } from 'react-router-dom'
import { AdminRoute } from '../components/AdminRoute'
import { ProtectedRoute } from '../components/ProtectedRoute'
import { AdminLayout } from '../layouts/AdminLayout'
import { AppLayout } from '../layouts/AppLayout'
import { AuthLayout } from '../layouts/AuthLayout'
import { PublicLayout } from '../layouts/PublicLayout'

// Lazy-loaded pages
const HomePage = lazy(() => import('../pages/HomePage').then(m => ({ default: m.HomePage })))
const LoginPage = lazy(() => import('../pages/LoginPage').then(m => ({ default: m.LoginPage })))
const RegisterPage = lazy(() => import('../pages/RegisterPage').then(m => ({ default: m.RegisterPage })))
const DepartmentDetailPage = lazy(() => import('../pages/DepartmentDetailPage').then(m => ({ default: m.DepartmentDetailPage })))
const MajorDetailPage = lazy(() => import('../pages/MajorDetailPage').then(m => ({ default: m.MajorDetailPage })))
const SubjectDetailPage = lazy(() => import('../pages/SubjectDetailPage').then(m => ({ default: m.SubjectDetailPage })))
const DocumentDetailPage = lazy(() => import('../pages/DocumentDetailPage').then(m => ({ default: m.DocumentDetailPage })))
const MyResourcesPage = lazy(() => import('../pages/MyResourcesPage').then(m => ({ default: m.MyResourcesPage })))
const MyNotebooksPage = lazy(() => import('../pages/MyNotebooksPage').then(m => ({ default: m.MyNotebooksPage })))
const NotebookDetailPage = lazy(() => import('../pages/NotebookDetailPage').then(m => ({ default: m.NotebookDetailPage })))
const AdminTaxonomyPage = lazy(() => import('../pages/AdminTaxonomyPage').then(m => ({ default: m.AdminTaxonomyPage })))

function PageFallback() {
  return (
    <div className="flex items-center justify-center py-20 min-h-[40vh]">
      <div className="h-8 w-8 animate-spin rounded-full border-3 border-slate-200 border-t-sky-600" />
    </div>
  )
}

function withSuspense(Component: ComponentType) {
  return (
    <Suspense fallback={<PageFallback />}>
      <Component />
    </Suspense>
  )
}

const router = createBrowserRouter([
  // ── Auth pages (standalone, no sidebar) ─────────────────────────
  {
    element: <AuthLayout />,
    children: [
      { path: '/login', element: withSuspense(LoginPage) },
      { path: '/register', element: withSuspense(RegisterPage) },
    ],
  },
  // ── Public pages (with sidebar) ──────────────────────────────────
  {
    element: <PublicLayout />,
    children: [
      { path: '/', element: withSuspense(HomePage) },
      { path: '/departments/:id', element: withSuspense(DepartmentDetailPage) },
      { path: '/majors/:id', element: withSuspense(MajorDetailPage) },
      { path: '/subjects/:id', element: withSuspense(SubjectDetailPage) },
      { path: '/documents/:id', element: withSuspense(DocumentDetailPage) },
    ],
  },
  // ── Protected pages (with AppLayout + auth guard) ────────────────
  {
    element: (
      <ProtectedRoute>
        <AppLayout />
      </ProtectedRoute>
    ),
    children: [
      { path: '/me/resources', element: withSuspense(MyResourcesPage) },
      { path: '/me/workspace', element: withSuspense(MyNotebooksPage) },
      { path: '/me/workspace/:notebookId', element: withSuspense(NotebookDetailPage) },
    ],
  },
  // ── Admin pages ───────────────────────────────────────────────────
  {
    element: (
      <AdminRoute>
        <AdminLayout />
      </AdminRoute>
    ),
    children: [
      { path: '/admin/taxonomy', element: withSuspense(AdminTaxonomyPage) },
    ],
  },
])

export function AppRouter() {
  return <RouterProvider router={router} />
}

