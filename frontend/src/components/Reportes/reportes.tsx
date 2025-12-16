import { useState } from "react"
import { Button, Container, Flex, Heading, Input, Text } from "@chakra-ui/react"
import { Select, SelectItem } from "@/components/ui/select"
import useAuth from "@/hooks/useAuth"
import React from "react"

function Reportes() {
  const { user } = useAuth()
  const isAdmin = !!(user?.is_superuser || user?.id_rol === 1)
  const [tipo, setTipo] = useState<string>("proveedores")
  const [formato, setFormato] = useState<string>("pdf")
  const [q, setQ] = useState<string>("")
  const [estado, setEstado] = useState<string>("") // "" | "true" | "false"
  const [desde, setDesde] = useState<string>("")
  const [hasta, setHasta] = useState<string>("")
  const [roles, setRoles] = useState<Array<{ id_rol: number; nombre_rol: string }>>([])
  const [sucursales, setSucursales] = useState<Array<{ id_sucursal: number; nombre: string }>>([])
  const [rolId, setRolId] = useState<string>("")
  const [sucursalId, setSucursalId] = useState<string>("")
  const [bodegas, setBodegas] = useState<Array<{ id_bodega: number; nombre: string; id_sucursal: number }>>([])
  const [proveedores, setProveedores] = useState<Array<{ id_proveedor: number; nombre: string }>>([])
  const [bodegaId, setBodegaId] = useState<string>("")
  const [proveedorId, setProveedorId] = useState<string>("")

  // Cargar listas para filtros de Usuarios (solo si es admin y el tipo es usuarios)
  React.useEffect(() => {
    if (!isAdmin || tipo !== "usuarios") return
    const ctrl = new AbortController()
    const token = localStorage.getItem("access_token")
    const headers: Record<string, string> = token ? { Authorization: `Bearer ${token}` } : {}
    ;(async () => {
      try {
        const [rRes, sRes] = await Promise.all([
          fetch("/api/v1/roles/?skip=0&limit=1000", { credentials: "include", signal: ctrl.signal, headers }),
          fetch("/api/v1/sucursales/?skip=0&limit=1000", { credentials: "include", signal: ctrl.signal, headers }),
        ])
        if (rRes.ok) {
          const data = await rRes.json()
          setRoles(data?.data ?? [])
        }
        if (sRes.ok) {
          const data = await sRes.json()
          setSucursales(data?.data ?? [])
        }
      } catch (_) {
        /* ignore */
      }
    })()
    return () => ctrl.abort()
  }, [isAdmin, tipo])

  // Cargar filtros de Lotes
  React.useEffect(() => {
    if (tipo !== "lotes") return
    const ctrl = new AbortController()
    const token = localStorage.getItem("access_token")
    const headers: Record<string, string> = token ? { Authorization: `Bearer ${token}` } : {}
    ;(async () => {
      try {
        const [sRes, bRes, pRes] = await Promise.all([
          fetch("/api/v1/sucursales/?skip=0&limit=1000", { credentials: "include", signal: ctrl.signal, headers }),
          fetch("/api/v1/bodegas/?skip=0&limit=1000", { credentials: "include", signal: ctrl.signal, headers }),
          fetch("/api/v1/proveedores/?skip=0&limit=1000", { credentials: "include", signal: ctrl.signal, headers }),
        ])
        if (sRes.ok) setSucursales((await sRes.json())?.data ?? [])
        if (bRes.ok) setBodegas((await bRes.json())?.data ?? [])
        if (pRes.ok) setProveedores((await pRes.json())?.data ?? [])
      } catch (_) { /* ignore */ }
    })()
    return () => ctrl.abort()
  }, [tipo])

  const tipos = ["proveedores", "lotes"].concat(isAdmin ? ["usuarios"] : [])

  const handleDescargar = async () => {
    const params = new URLSearchParams({ formato })
    if (q) params.set("q", q)
    if (estado) params.set("estado", estado)
    if (desde) params.set("desde", desde)
    if (hasta) params.set("hasta", hasta)
    if (tipo === "usuarios") {
      if (rolId) params.set("id_rol", rolId)
      if (sucursalId) params.set("id_sucursal", sucursalId)
    }
    if (tipo === "lotes") {
      if (sucursalId) params.set("id_sucursal", sucursalId)
      if (bodegaId) params.set("id_bodega", bodegaId)
      if (proveedorId) params.set("id_proveedor", proveedorId)
    }
    const url = `/api/v1/reportes/${tipo}?${params.toString()}`
    const token = localStorage.getItem("access_token")
    const headers: Record<string, string> = {}
    if (token) headers["Authorization"] = `Bearer ${token}`
    // Help servers/tools set the correct content type
    if (formato === "excel") {
      headers["Accept"] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    } else {
      headers["Accept"] = "application/pdf"
    }
    const res = await fetch(url, { credentials: "include", headers })
    if (!res.ok) {
      alert("Error al generar reporte")
      return
    }
    const blob = await res.blob()
    const urlObj = URL.createObjectURL(blob)
    const a = document.createElement("a")
    // Try to read filename from header, fallback to constructed name
    const cd = res.headers.get("Content-Disposition") || ""
    const match = cd.match(/filename\*=UTF-8''([^;]+)|filename=([^;]+)/)
    const headerName = match ? decodeURIComponent((match[1] || match[2]).replace(/"/g, "").trim()) : undefined
    const fallback = `${tipo}.${formato === "excel" ? "xlsx" : "pdf"}`
    a.href = urlObj
    a.download = headerName || fallback
    document.body.appendChild(a)
    a.click()
    a.remove()
    // Revoke after a tick to avoid truncating the download in some browsers
    setTimeout(() => URL.revokeObjectURL(urlObj), 1500)
  }

  return (
    <Container maxW="full" pt={12}>
      <Heading size="lg" mb={6}>Reportes</Heading>
      <Flex direction="column" gap={6} maxW="900px">
        <Flex gap={4} align="center" wrap="wrap">
          <Text minW="70px">Buscar</Text>
          <Input
            placeholder="Nombre, NIT, email o teléfono"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            size="sm"
            maxW="360px"
          />
          <Text minW="70px">Estado</Text>
          <Select
            placeholder="Todos"
            value={estado}
            onValueChange={(value) => setEstado(value)}
            style={{ maxWidth: "220px", color: "gray.600", backgroundColor: "white", borderRadius: "4px", border: "2px solid #e2e8f0", padding: "8px 8px", fontSize: "14px" }}
          >
            <SelectItem value="">Todos</SelectItem>
            <SelectItem value="true">Activos</SelectItem>
            <SelectItem value="false">Inactivos</SelectItem>
          </Select>
          <Text minW="70px">Desde</Text>
          <Input type="date" value={desde} onChange={(e) => setDesde(e.target.value)} size="sm" />
          <Text minW="50px">Hasta</Text>
          <Input type="date" value={hasta} onChange={(e) => setHasta(e.target.value)} size="sm" />
        </Flex>
        {isAdmin && tipo === "usuarios" && (
          <Flex gap={4} align="center" wrap="wrap">
            <Text minW="70px">Rol</Text>
            <Select
              placeholder="Todos"
              value={rolId}
              onValueChange={(value) => setRolId(value)}
              style={{ maxWidth: "260px", color: "gray.600", backgroundColor: "white", borderRadius: "4px", border: "2px solid #e2e8f0", padding: "8px 8px", fontSize: "14px" }}
            >
              <SelectItem value="">Todos</SelectItem>
              {roles.map((r) => (
                <SelectItem key={r.id_rol} value={String(r.id_rol)}>
                  {r.nombre_rol}
                </SelectItem>
              ))}
            </Select>
            <Text minW="70px">Sucursal</Text>
            <Select
              placeholder="Todas"
              value={sucursalId}
              onValueChange={(value) => setSucursalId(value)}
              style={{ maxWidth: "260px", color: "gray.600", backgroundColor: "white", borderRadius: "4px", border: "2px solid #e2e8f0", padding: "8px 8px", fontSize: "14px" }}
            >
              <SelectItem value="">Todas</SelectItem>
              {sucursales.map((s) => (
                <SelectItem key={s.id_sucursal} value={String(s.id_sucursal)}>
                  {s.nombre}
                </SelectItem>
              ))}
            </Select>
          </Flex>
        )}
        {tipo === "lotes" && (
          <Flex gap={4} align="center" wrap="wrap">
            <Text minW="70px">Sucursal</Text>
            <Select
              placeholder="Todas"
              value={sucursalId}
              onValueChange={(value) => {
                setSucursalId(value)
                setBodegaId("")
              }}
              style={{ maxWidth: "260px", color: "gray.600", backgroundColor: "white", borderRadius: "4px", border: "2px solid #e2e8f0", padding: "8px 8px", fontSize: "14px" }}
            >
              <SelectItem value="">Todas</SelectItem>
              {sucursales.map((s) => (
                <SelectItem key={s.id_sucursal} value={String(s.id_sucursal)}>
                  {s.nombre}
                </SelectItem>
              ))}
            </Select>
            <Text minW="70px">Bodega</Text>
            <Select
              placeholder="Todas"
              value={bodegaId}
              onValueChange={(value) => setBodegaId(value)}
              style={{ maxWidth: "260px", color: "gray.600", backgroundColor: "white", borderRadius: "4px", border: "2px solid #e2e8f0", padding: "8px 8px", fontSize: "14px" }}
            >
              <SelectItem value="">Todas</SelectItem>
              {bodegas
                .filter((b) => !sucursalId || String(b.id_sucursal) === sucursalId)
                .map((b) => (
                  <SelectItem key={b.id_bodega} value={String(b.id_bodega)}>
                    {b.nombre}
                  </SelectItem>
                ))}
            </Select>
            <Text minW="70px">Proveedor</Text>
            <Select
              placeholder="Todos"
              value={proveedorId}
              onValueChange={(value) => setProveedorId(value)}
              style={{ maxWidth: "260px", color: "gray.600", backgroundColor: "white", borderRadius: "4px", border: "2px solid #e2e8f0", padding: "8px 8px", fontSize: "14px" }}
            >
              <SelectItem value="">Todos</SelectItem>
              {proveedores.map((p) => (
                <SelectItem key={p.id_proveedor} value={String(p.id_proveedor)}>
                  {p.nombre}
                </SelectItem>
              ))}
            </Select>
          </Flex>
        )}
        <Flex gap={3} align="center">
          <Text>Tipo</Text>
          <Select
            placeholder="Selecciona tipo"
            value={tipo}
            onValueChange={(value) => {
              setTipo(value)
              if (value !== "lotes") setFormato("pdf")
            }}
            style={{ maxWidth: "300px",  color: "gray.600", backgroundColor: "white", borderRadius: "4px", border: "2px solid #e2e8f0", padding: "8px 8px", fontSize: "14px" }}
          >
            {tipos.map((t) => (
              <SelectItem key={t} value={t}>{t}</SelectItem>
            ))}
          </Select>
        </Flex>
        <Flex gap={3} align="center">
          <Text>Formato</Text>
          <Select
            placeholder="Selecciona formato"
            value={formato}
            onValueChange={(value) => setFormato(value)}
            style={{ maxWidth: "300px",  color: "gray.600", backgroundColor: "white", borderRadius: "4px", border: "2px solid #e2e8f0", padding: "8px 8px", fontSize: "14px" }}
          >
            <SelectItem value="pdf">PDF</SelectItem>
            {tipo === "lotes" && <SelectItem value="excel">Excel</SelectItem>}
          </Select>
        </Flex>
        <Flex gap={3}>
          <Button onClick={handleDescargar}>Descargar</Button>
          <Button
            variant="subtle"
            onClick={() => {
              setQ("")
              setEstado("")
              setDesde("")
              setHasta("")
            }}
          >
            Limpiar filtros
          </Button>
        </Flex>
      </Flex>
    </Container>
  )
}

export default Reportes
