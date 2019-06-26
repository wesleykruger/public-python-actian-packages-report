# public-python-actian-packages-report

This is a command line application designed to report on currently deployed Actian packages across multiple cloud environments.
It will prompt the user for their environment username/password, and will then send a request to Actian's REST API to retrieve the desired data.
Because the result is in XML, the program will use xml.etree.ElementTree to parse the returned data.

Users can either list all packages deployed in an environment, or they can see all jobs run using a particular package.

The application is currently designed to reach three environments, but that can be easily adjusted to meet each user's need.

## Packages used
* Requests - Excellent tool for API requests. Because Actian uses digest authentication on its API, this saved a lot of headaches.
* PrettyTable - Used to format the table within the terminal for a more readable presentation.
