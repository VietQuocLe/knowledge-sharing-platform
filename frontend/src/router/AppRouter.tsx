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
import { ResourceDetailPage } from '../pages/ResourceDetailPage'
// import { ResourceUploadPage } from '../pages/ResourceUploadPage'  // [PAUSED - Admin branch]
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
      // Both /resources/:id and /documents/:id point to the same page
      { path: '/resources/:id', element: <ResourceDetailPage /> },
      { path: '/documents/:id', element: <ResourceDetailPage /> },
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
      // { path: '/resources/create', element: <ResourceCreatePage /> },  // [PAUSED - Admin branch]
      // { path: '/resources/:id/upload', element: <ResourceUploadPage /> },  // [PAUSED - Admin branch]
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
