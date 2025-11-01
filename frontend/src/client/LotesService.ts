import type { CancelablePromise } from "./core/CancelablePromise"
import { OpenAPI } from "./core/OpenAPI"
import { request as __request } from "./core/request"

export interface LoteCreate {
  numero_lote: string
  fecha_fabricacion: string
  fecha_vencimiento: string
  estado: string
  observaciones?: string
  id_proveedor: number
  id_bodega: number
}

export interface LoteUpdate {
  numero_lote?: string
  fecha_fabricacion?: string
  fecha_vencimiento?: string
  estado?: string
  observaciones?: string
  id_proveedor?: number
  id_bodega?: number
}

export interface LotePublic {
  id_lote: number
  numero_lote: string
  fecha_fabricacion: string
  fecha_vencimiento: string
  estado: string
  observaciones?: string
  id_proveedor: number
  id_bodega: number | null
  fecha_registro: string
  proveedor_nombre?: string | null
  bodega_nombre?: string | null
  producto_nombre?: string | null
  stock_total?: number | null
}

export interface LotesPublic {
  data: LotePublic[]
  count: number
}

export interface LotesStats {
  total_lotes: number
  activos: number
  vencidos: number
  proximos_a_vencer: number
}

export interface RecepcionProductoItem {
  nombre_comercial: string
  nombre_generico?: string
  codigo_interno?: string
  codigo_barras?: string
  forma_farmaceutica: string
  concentracion: string
  presentacion: string
  unidad_medida: string
  cantidad: number
  stock_minimo: number
  stock_maximo: number
}

export interface RecepcionLotePayload {
  lote: LoteCreate
  items: RecepcionProductoItem[]
}

export interface DistribucionBodegaItem {
  id_bodega: number
  items: RecepcionProductoItem[]
}

export interface RecepcionDistribuidaPayload {
  lote_base: LoteCreate
  distribuciones: DistribucionBodegaItem[]
}

export interface RecepcionResponse {
  lote: LotePublic
  productos_ids: number[]
}

export interface RecepcionDistribuidaResponse {
  numero_lote_base: string
  lotes_creados: Array<{
    id_lote: number
    numero_lote: string
    bodega: string
  }>
  productos_creados: Array<{
    id_producto: number
    nombre: string
    cantidad: number
    bodega_id: number
    bodega_nombre: string
    numero_lote: string
  }>
  total_productos: number
  bodegas_utilizadas: number
  message: string
}

export class LotesService {
  public static readLotes(data: {
    skip?: number
    limit?: number
    q?: string
    estado?: string
    id_bodega?: number
    id_proveedor?: number
  }): CancelablePromise<LotesPublic> {
    return __request(OpenAPI, {
      method: "GET",
      url: "/api/v1/lotes/",
      query: {
        skip: data.skip,
        limit: data.limit,
        q: data.q,
        estado: data.estado,
        id_bodega: data.id_bodega,
        id_proveedor: data.id_proveedor,
      },
    })
  }

  public static readLote(data: { id: number }): CancelablePromise<LotePublic> {
    return __request(OpenAPI, {
      method: "GET",
      url: `/api/v1/lotes/${data.id}`,
    })
  }

  public static createLote(data: { requestBody: LoteCreate }): CancelablePromise<LotePublic> {
    return __request(OpenAPI, {
      method: "POST",
      url: "/api/v1/lotes/",
      body: data.requestBody,
      mediaType: "application/json",
    })
  }

  public static updateLote(data: {
    id: number
    requestBody: LoteUpdate
  }): CancelablePromise<LotePublic> {
    return __request(OpenAPI, {
      method: "PUT",
      url: `/api/v1/lotes/${data.id}`,
      body: data.requestBody,
      mediaType: "application/json",
    })
  }

  public static getLotesStats(): CancelablePromise<LotesStats> {
    return __request(OpenAPI, {
      method: "GET",
      url: "/api/v1/lotes/stats",
      errors: {
        422: "Validation Error",
      },
    })
  }

  public static recepcionLote(data: {
    requestBody: RecepcionLotePayload
  }): CancelablePromise<RecepcionResponse> {
    return __request(OpenAPI, {
      method: "POST",
      url: "/api/v1/lotes/recepcion",
      body: data.requestBody,
      mediaType: "application/json",
      errors: {
        400: "Bad Request",
        409: "Capacidad Insuficiente",
        507: "Capacidad Insuficiente en Sucursal",
      },
    })
  }

  public static recepcionDistribuida(data: {
    requestBody: RecepcionDistribuidaPayload
  }): CancelablePromise<RecepcionDistribuidaResponse> {
    return __request(OpenAPI, {
      method: "POST",
      url: "/api/v1/lotes/recepcion-distribuida",
      body: data.requestBody,
      mediaType: "application/json",
      errors: {
        400: "Bad Request",
        409: "Capacidad Insuficiente al Distribuir",
      },
    })
  }
}

