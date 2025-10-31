import { Grid, GridItem, Heading, VStack } from "@chakra-ui/react"
import useAuth from "@/hooks/useAuth"
import { useAlcance } from "@/hooks/useAlcance"
import RecepcionForm from "./RecepcionForm"
import ResumenPanel from "./ResumenPanel"
import LotesList from "./LotesList"

const RecepcionLotes = () => {
  const { user } = useAuth()
  const alcance = useAlcance()

  return (
    <VStack align="stretch" gap={4} w="full">
      <Heading size="xl">Recepción de lotes</Heading>
      <Grid templateColumns={{ base: "1fr", lg: "2fr 1fr" }} gap={6}>
        <GridItem>
          <RecepcionForm alcance={alcance} />
        </GridItem>
        <GridItem>
          <ResumenPanel user={user ?? undefined} alcance={alcance} />
        </GridItem>
      </Grid>
      <LotesList />
    </VStack>
  )
}

export default RecepcionLotes


