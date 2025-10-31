import { Card, Flex, SimpleGrid, Text, SkeletonText } from "@chakra-ui/react"
import { FiBox, FiCheckCircle, FiPackage, FiTrendingUp } from "react-icons/fi"
import { useBodegas, type BodegasStats } from "@/hooks/useBodegas"
import { useQuery } from "@tanstack/react-query"

const StatsCards = () => {
  const { statsQuery } = useBodegas()
  const { data: stats, isLoading } = useQuery(statsQuery)

  if (isLoading) {
    return (
      <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} gap={4} mb={6}>
        {Array.from({ length: 4 }).map((_, index) => (
          <Card.Root key={index} p={4}>
            <Card.Body>
              <SkeletonText noOfLines={2} spacing="2" skeletonHeight="4" />
            </Card.Body>
          </Card.Root>
        ))}
      </SimpleGrid>
    )
  }

  const statsData = stats as BodegasStats | undefined

  const statsCards = [
    {
      title: "Total Bodegas",
      value: statsData?.total_bodegas || 0,
      icon: FiBox,
      color: "blue",
    },
    {
      title: "Operativas",
      value: statsData?.operativas || 0,
      icon: FiCheckCircle,
      color: "green",
    },
    {
      title: "Capacidad Total",
      value: statsData?.capacidad_total || 0,
      icon: FiPackage,
      color: "purple",
    },
    {
      title: "Ocupación",
      value: statsData?.ocupacion_total
        ? `${statsData.ocupacion_total.toFixed(1)}%`
        : "0%",
      icon: FiTrendingUp,
      color: "green",
    },
  ]

  return (
    <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} gap={4} mb={6}>
      {statsCards.map((stat, index) => (
        <Card.Root key={index} p={4}>
          <Card.Body>
            <Flex align="center" justify="space-between" mb={2}>
              <Text fontSize="sm" color="gray.500">
                {stat.title}
              </Text>
              <stat.icon fontSize="20px" color={`${stat.color}.500`} />
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

