import { Card, Flex, SimpleGrid, Text, Icon } from "@chakra-ui/react"
import { useQuery } from "@tanstack/react-query"
import { FiPackage, FiAlertTriangle, FiBox } from "react-icons/fi"
import { BsFillCircleFill } from "react-icons/bs"

import { LotesService, type LotesStats } from "@/client"
import { useBodegas, type BodegasStats } from "@/hooks/useBodegas"

interface StatsCardsProps {
  id_sucursal?: number | null
}

const StatsCards = ({ id_sucursal }: StatsCardsProps) => {
  // Query para stats de lotes (ya filtra automáticamente por sucursal en el backend)
  const { data: lotesStats, isLoading: lotesLoading } = useQuery<LotesStats>({
    queryFn: async () => {
      try {
        const response = await LotesService.getLotesStats()
        return response
      } catch (error) {
        console.error("Error fetching lotes stats:", error)
        throw error
      }
    },
    queryKey: ["lotes-stats"],
    refetchOnWindowFocus: true,
    refetchInterval: 60000, // Refrescar cada minuto
  })

  // Query para stats de bodegas con filtro de sucursal
  const { getStatsQuery } = useBodegas()
  const { data: bodegasStats, isLoading: bodegasLoading } = useQuery<BodegasStats>(
    getStatsQuery(id_sucursal)
  )

  const isLoading = lotesLoading || bodegasLoading

  const statsData = [
    {
      title: "Lotes Activos",
      value: lotesStats?.activos || 0,
      icon: BsFillCircleFill,
      color: "green",
    },
    {
      title: "Próximos a vencer",
      value: lotesStats?.proximos_a_vencer || 0,
      icon: FiAlertTriangle,
      color: "yellow",
    },
    {
      title: "Total Bodegas",
      value: bodegasStats?.total_bodegas || 0,
      icon: FiBox,
      color: "blue",
    },
  ]

  // Mostrar loading state
  if (isLoading) {
    return (
      <SimpleGrid columns={{ base: 1, md: 3 }} gap={4} mb={6}>
        {Array.from({ length: 3 }).map((_, index) => (
          <Card.Root key={index} p={4}>
            <Card.Body>
              <Flex align="center" justify="space-between" mb={2}>
                <Text fontSize="sm" color="gray.500">
                  Cargando...
                </Text>
                <Icon as={FiPackage} fontSize="20px" color="gray.300" />
              </Flex>
              <Text fontSize="2xl" fontWeight="bold" color="gray.300">
                --
              </Text>
            </Card.Body>
          </Card.Root>
        ))}
      </SimpleGrid>
    )
  }

  return (
    <SimpleGrid columns={{ base: 1, md: 3 }} gap={4} mb={6}>
      {statsData.map((stat, index) => (
        <Card.Root key={index} p={4}>
          <Card.Body>
            <Flex align="center" justify="space-between" mb={2}>
              <Text fontSize="sm" color="gray.500">
                {stat.title}
              </Text>
              <Icon as={stat.icon} fontSize="20px" color={`${stat.color}.500`} />
            </Flex>
            <Text fontSize="2xl" fontWeight="bold" color={`${stat.color}.600`}>
              {stat.value}
            </Text>
          </Card.Body>
        </Card.Root>
      ))}
    </SimpleGrid>
  )
}

export default StatsCards
