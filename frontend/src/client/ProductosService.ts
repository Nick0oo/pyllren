import type { CancelablePromise } from './core/CancelablePromise'
import { OpenAPI } from './core/OpenAPI'
import { request as __request } from './core/request'

export interface ProductoPublic {
  id_producto: number
  nombre_comercial: string
  nombre_generico?: string
  codigo_interno?: string
  codigo_barras?: string
  forma_farmaceutica: string
  concentracion: string
  presentacion: string
  unidad_medida: string
  cantidad_total: number
  cantidad_disponible: number
  stock_minimo: number
  stock_maximo: number
  estado: boolean
  id_lote: number
  numero_lote?: string | null
  bodega_nombre?: string | null
  fecha_creacion: string
}

export interface ProductosPublic {
  data: ProductoPublic[]
  count: number
}

export interface ProductosStats {
  total_productos: number
  stock_total: number
  lotes_activos: number
  productos_criticos: number
}

export class ProductosService {
  public static readProductos(data: { skip?: number; limit?: number; q?: string; id_sucursal?: number | null } = {}): CancelablePromise<ProductosPublic> {
    return __request(OpenAPI, {
      method: 'GET',
      url: '/api/v1/productos/',
      query: {
        skip: data.skip,
        limit: data.limit,
        q: data.q,
        id_sucursal: data.id_sucursal,
      },
    })
  }

  public static readProducto(data: { id: number }): CancelablePromise<ProductoPublic> {
    return __request(OpenAPI, {
      method: 'GET',
      url: `/api/v1/productos/${data.id}`,
    })
  }

  public static readStats(data: { id_sucursal?: number | null } = {}): CancelablePromise<ProductosStats> {
    return __request(OpenAPI, {
      method: 'GET',
      url: '/api/v1/productos/stats',
      query: {
        id_sucursal: data.id_sucursal,
      },
      errors: {
        422: 'Validation Error',
      },
    })
  }
}
