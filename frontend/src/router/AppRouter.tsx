import { createBrowserRouter, RouterProvider } from 'react-router-dom'
import { AdminRoute } from '../components/AdminRoute'
import { ProtectedRoute } from '../components/ProtectedRoute'
import { AdminLayout } from '../layouts/AdminLayout'
import { AppLayout } from '../layouts/AppLayout'
import { PublicLayout } from '../layouts/PublicLayout'
// import { AdminModerationPage } from '../pages/AdminModerationPage'  // [PAUSED - Admin branch]
import { AdminTaxonomyPage } from '../pages/AdminTaxonomyPage'
import { DepartmentDetailPage } from '../pages/DepartmentDetailPage'
import { DepartmentsPage } from '../pages/DepartmentsPage'
import { HomePage } from '../pages/HomePage'
import { LoginPage } from '../pages/LoginPage'
import { MajorDetailPage } from '../pages/MajorDetailPage'
import { MyResourcesPage } from '../pages/MyResourcesPage'
import { RegisterPage } from '../pages/RegisterPage'
// import { ResourceCreatePage } from '../pages/ResourceCreatePage'  // [PAUSED - Admin branch]
import { DocumentDetailPage } from '../pages/DocumentDetailPage'
import { SubjectDetailPage } from '../pages/SubjectDetailPage'

const router = createBrowserRouter([
  {
    element: <PublicLayout />,
    children: [
      { path: '/', element: <HomePage /> },
      { path: '/login', element: <LoginPage /> },
      { path: '/register', element: <RegisterPage /> },
      { path: '/departments', element: <DepartmentsPage /> },
      { path: '/departments/:id', element: <DepartmentDetailPage /> },
      { path: '/majors/:id', element: <MajorDetailPage /> },
      { path: '/subjects/:id', element: <SubjectDetailPage /> },
      { path: '/documents/:id', element: <DocumentDetailPage /> },
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
    ],
  },
  {
    element: (
      <AdminRoute>
        <AdminLayout />
      </AdminRoute>
    ),
    children: [
      // { path: '/admin/moderation', element: <AdminModerationPage /> },  // [PAUSED - Admin branch]
      { path: '/admin/taxonomy', element: <AdminTaxonomyPage /> },
    ],
  },
])

export function AppRouter() {
  return <RouterProvider router={router} />
}
