import { createBrowserRouter, RouterProvider } from 'react-router-dom'
import { AdminRoute } from '../components/AdminRoute'
import { ProtectedRoute } from '../components/ProtectedRoute'
import { AdminLayout } from '../layouts/AdminLayout'
import { AppLayout } from '../layouts/AppLayout'
import { PublicLayout } from '../layouts/PublicLayout'
import { AdminModerationPage } from '../pages/AdminModerationPage'
import { AdminTaxonomyPage } from '../pages/AdminTaxonomyPage'
import { DepartmentDetailPage } from '../pages/DepartmentDetailPage'
import { HomePage } from '../pages/HomePage'
import { LoginPage } from '../pages/LoginPage'
import { MyResourcesPage } from '../pages/MyResourcesPage'
import { RegisterPage } from '../pages/RegisterPage'
import { ResourceCreatePage } from '../pages/ResourceCreatePage'
import { ResourceDetailPage } from '../pages/ResourceDetailPage'
import { ResourceUploadPage } from '../pages/ResourceUploadPage'
import { SubjectDetailPage } from '../pages/SubjectDetailPage'

const router = createBrowserRouter([
  {
    element: <PublicLayout />,
    children: [
      { path: '/', element: <HomePage /> },
      { path: '/login', element: <LoginPage /> },
      { path: '/register', element: <RegisterPage /> },
      { path: '/departments/:id', element: <DepartmentDetailPage /> },
      { path: '/subjects/:id', element: <SubjectDetailPage /> },
      { path: '/resources/:id', element: <ResourceDetailPage /> },
    ],
  },
  {
    element: (
      <ProtectedRoute>
        <AppLayout />
      </ProtectedRoute>
    ),
    children: [
      { path: '/me/resources', element: <MyResourcesPage /> },
      { path: '/resources/new', element: <ResourceCreatePage /> },
      { path: '/resources/:id/upload', element: <ResourceUploadPage /> },
    ],
  },
  {
    element: (
      <AdminRoute>
        <AdminLayout />
      </AdminRoute>
    ),
    children: [
      { path: '/admin/moderation', element: <AdminModerationPage /> },
      { path: '/admin/taxonomy', element: <AdminTaxonomyPage /> },
    ],
  },
])

export function AppRouter() {
  return <RouterProvider router={router} />
}
