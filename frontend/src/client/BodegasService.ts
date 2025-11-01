import type { CancelablePromise } from "./core/CancelablePromise"
import { OpenAPI } from "./core/OpenAPI"
import { request as __request } from "./core/request"

export interface BodegaPublic {
  id_bodega: number
  nombre: string
  descripcion?: string
  tipo: string
  estado: boolean
  id_sucursal: number
}

export interface BodegasPublic {
  data: BodegaPublic[]
  count: number
}

export class BodegasService {
  public static readBodegas(data: {
    skip?: number
    limit?: number
  }): CancelablePromise<BodegasPublic> {
    return __request(OpenAPI, {
      method: "GET",
      url: "/api/v1/bodegas/",
      query: {
        skip: data.skip,
        limit: data.limit,
      },
    })
  }

  public static readBodega(data: { id: number }): CancelablePromise<BodegaPublic> {
    return __request(OpenAPI, {
      method: "GET",
      url: `/api/v1/bodegas/${data.id}`,
    })
  }
}

export interface BodegasStats {
  total_bodegas: number
}

export class BodegasStatsService {
  public static getBodegasStats(data?: {
    id_sucursal?: number
  }): CancelablePromise<BodegasStats> {
    return __request(OpenAPI, {
      method: 'GET',
      url: '/api/v1/bodegas/stats/',
      query: {
        id_sucursal: data?.id_sucursal,
      },
    })
  }
}