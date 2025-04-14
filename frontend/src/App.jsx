import React from 'react';
import { ChakraProvider, Box, Heading, VStack, Divider, extendTheme, CSSReset } from '@chakra-ui/react';
import ServiceControl from './features/control/ServiceControl'; // Adjust path if needed

// Optional: Define or extend Chakra theme
const theme = extendTheme({
  // Example: Add custom colors or component styles
  // colors: {
  //   brand: { 900: '#1a365d', 800: '#153e75', 700: '#2a69ac', },
  // },
});

function App() {
  return (
      <ChakraProvider theme={theme}>
        <CSSReset /> {/* Good practice to include CSSReset */}
        <Box p={{ base: 3, md: 6 }} minH="100vh" bg="gray.50"> {/* Add basic page background */}
          <Box maxWidth="container.lg" mx="auto" bg="white" p={6} borderRadius="lg" shadow="base"> {/* Content wrapper */}
            <VStack spacing={6} align="stretch">
              <Heading textAlign="center" size="lg" mb={4} color="teal.600">
                OmniCore AI Platform - PoC Control Panel
              </Heading>

              {/* Service Control Section */}
              <ServiceControl serviceName="stt" title="Speech-to-Text (STT) Service" />

              <Divider my={4}/>

              {/* Placeholder for other features */}
              <Box p={5} borderWidth="1px" borderRadius="lg" bg="gray.50">
                <Heading size="md" mb={3} color="gray.600">Future Features</Heading>
                <Text color="gray.700">TTS Control, Diary, Subtitle Tools, etc., will appear here.</Text>
              </Box>

            </VStack>
          </Box>
        </Box>
      </ChakraProvider>
  );
}

export default App;