import { SimpleGrid, Text, Skeleton } from "@chakra-ui/react"
import type { BodegaPublicExtended, BodegaPublic } from "@/hooks/useBodegas"
import BodegaCard from "./BodegaCard"

type Props = {
  bodegas: (BodegaPublicExtended | BodegaPublic)[]
  isLoading: boolean
}

const BodegasList = ({ bodegas, isLoading }: Props) => {
  if (isLoading) {
    return (
      <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} gap={4}>
        {Array.from({ length: 6 }).map((_, index) => (
          <Skeleton key={index} height="300px" borderRadius="md" />
        ))}
      </SimpleGrid>
    )
  }

  if (bodegas.length === 0) {
    return (
      <Text color="gray.600" textAlign="center" py={8}>
        No hay bodegas registradas
      </Text>
    )
  }

  return (
    <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} gap={4}>
      {bodegas.map((bodega) => (
        <BodegaCard key={bodega.id_bodega} bodega={bodega} />
      ))}
    </SimpleGrid>
  )
}

export default BodegasList

