import { AuthForm } from '../features/auth/components/AuthForm'
import { ResourceList } from '../features/resources/components/ResourceList'
import { TaxonomyView } from '../features/taxonomy/components/TaxonomyView'

export function HomePage() {
  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-6 p-8">
      <h1 className="text-3xl font-bold text-slate-900">Knowledge Sharing Platform</h1>
      <p className="text-slate-600">Cấu trúc frontend đã được tái tổ chức theo feature-based.</p>
      <div className="grid gap-6 lg:grid-cols-[1fr_1.2fr]">
        <AuthForm />
        <div className="space-y-6">
          <ResourceList />
          <TaxonomyView />
        </div>
      </div>
    </div>
  )
}
