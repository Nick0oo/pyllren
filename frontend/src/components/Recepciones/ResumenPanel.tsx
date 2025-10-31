import { Box, Heading, Stack, Text, VStack } from "@chakra-ui/react"

type Props = {
  user?: { full_name?: string | null }
  alcance: { isAdmin: boolean }
}

const ResumenPanel = ({ user }: Props) => {
  const today = new Date()
  const fecha = today.toLocaleDateString()
  return (
    <VStack align="stretch" gap={4}>
      <Box p={4} borderWidth="1px" borderRadius="md" bg="bg.surface">
        <Heading size="lg" mb={4}>Resumen</Heading>
        <Stack gap={2}>
          <Text>
            <b>Fecha de ingreso:</b> {fecha}
          </Text>
          <Text>
            <b>Usuario:</b> {user?.full_name ?? ""}
          </Text>
          <Text>
            <b>Turno:</b> Mañana
          </Text>
        </Stack>
      </Box>
    </VStack>
  )
}

export default ResumenPanel


