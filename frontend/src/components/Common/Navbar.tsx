import { Flex, Image, useBreakpointValue } from "@chakra-ui/react"
import { Link } from "@tanstack/react-router"

import Logo from "/assets/images/PillREN.svg"
import UserMenu from "./UserMenu"
import NotificationBell from "./NotificationBell"

function Navbar() {
  const display = useBreakpointValue({ base: "none", md: "flex" })

  return (
    <Flex
      display={display}
      justify="space-between"
      position="sticky"
      color="white"
      align="center"
      bg="bg.muted"
      w="100%"
      top={0}
      p={4}
    >
      <Link to="/">
        <Image src={Logo} alt="Logo" maxW="xs" p={1} />
      </Link>
      <Flex gap={2} alignItems="center">
        <NotificationBell />
        <UserMenu />
      </Flex>
    </Flex>
  )
}

export default Navbar
