// Servicio temporal para Proveedores hasta que se regenere el cliente OpenAPI
import type { CancelablePromise } from './core/CancelablePromise'
import { OpenAPI } from './core/OpenAPI'
import { request as __request } from './core/request'

export interface ProveedorCreate {
  nombre: string
  nit: string
  telefono: string
  email: string
  direccion: string
  ciudad: string
  estado?: boolean
}

export interface ProveedorUpdate {
  nombre?: string
  nit?: string
  telefono?: string
  email?: string
  direccion?: string
  ciudad?: string
  estado?: boolean
}

export interface ProveedorPublic {
  id_proveedor: number
  nombre: string
  nit: string
  telefono: string
  email: string
  direccion: string
  ciudad: string
  estado: boolean
}

export interface ProveedoresPublic {
  data: ProveedorPublic[]
  count: number
}

export interface ProveedoresStats {
  total_proveedores: number
  activos: number
  inactivos: number
  total_lotes: number
}

export class ProveedoresService {
  public static readProveedores(data: {
    skip?: number
    limit?: number
    q?: string
    estado?: boolean
  } = {}): CancelablePromise<ProveedoresPublic> {
    return __request(OpenAPI, {
      method: 'GET',
      url: '/api/v1/proveedores/',
      query: {
        skip: data.skip,
        limit: data.limit,
        q: data.q,
        estado: data.estado
      },
      errors: {
        422: 'Validation Error'
      }
    })
  }

  public static createProveedor(data: {
    requestBody: ProveedorCreate
  }): CancelablePromise<ProveedorPublic> {
    return __request(OpenAPI, {
      method: 'POST',
      url: '/api/v1/proveedores/',
      body: data.requestBody,
      mediaType: 'application/json',
      errors: {
        422: 'Validation Error'
      }
    })
  }

  public static updateProveedor(data: {
    id: number
    requestBody: ProveedorUpdate
  }): CancelablePromise<ProveedorPublic> {
    return __request(OpenAPI, {
      method: 'PUT',
      url: '/api/v1/proveedores/{id}',
      path: {
        id: data.id
      },
      body: data.requestBody,
      mediaType: 'application/json',
      errors: {
        422: 'Validation Error'
      }
    })
  }

  public static deleteProveedor(data: {
    id: number
  }): CancelablePromise<{ message: string }> {
    return __request(OpenAPI, {
      method: 'DELETE',
      url: '/api/v1/proveedores/{id}',
      path: {
        id: data.id
      },
      errors: {
        422: 'Validation Error'
      }
    })
  }

  public static getProveedoresStats(): CancelablePromise<ProveedoresStats> {
    return __request(OpenAPI, {
      method: 'GET',
      url: '/api/v1/proveedores/stats',
      errors: {
        422: 'Validation Error'
      }
    })
  }
}
