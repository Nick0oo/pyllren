import { createFileRoute } from "@tanstack/react-router"
import Reportes from "@/components/Reportes/reportes"

// Debe ser la ruta pública '/reportes', no incluir el prefijo de carpeta.
export const Route = createFileRoute("/_layout/reportes")({
  component: Reportes,
})
