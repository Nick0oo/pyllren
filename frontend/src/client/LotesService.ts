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
  id_bodega: number
  fecha_registro: string
}

export interface LotesPublic {
  data: LotePublic[]
  count: number
}

export interface LotesStats {
  total_lotes: number
  activos: number
  vencidos: number
  próximos_a_vencer: number
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
}


