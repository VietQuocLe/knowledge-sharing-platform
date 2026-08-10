import { PublicLayout } from './layouts/PublicLayout'
import { AppRouter } from './router/AppRouter'
import './App.css'

function App() {
  return (
    <PublicLayout>
      <AppRouter />
    </PublicLayout>
  )
}

export default App
