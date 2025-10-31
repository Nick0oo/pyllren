import { createFileRoute, redirect } from "@tanstack/react-router"
import RecepcionLotes from "@/components/Recepciones/RecepcionLotes"
import { isLoggedIn } from "@/hooks/useAuth"

export const Route = createFileRoute("/_layout/recepciones")({
  beforeLoad: () => {
    if (!isLoggedIn()) throw redirect({ to: "/login" })
  },
  component: () => <RecepcionLotes />,
})

