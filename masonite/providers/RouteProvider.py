''' A RouteProvider Service Provider '''
from masonite.provider import ServiceProvider
import re
from pydoc import locate

class RouteProvider(ServiceProvider):

    def register(self):
        pass

    def boot(self, WebRoutes, Route, Request, Environ):
        for route in WebRoutes:
            router = Route
            request = Request
            # Compiles the given route to regex
            regex = router.compile_route_to_regex(route)

            '''
            |--------------------------------------------------------------------------
            | Make a better match for trailing slashes
            |--------------------------------------------------------------------------
            |
            | Sometimes a user will end with a trailing slash. Because the user might
            | create routes like `/url/route` and `/url/route/` and how the regex 
            | is compiled down, we may need to adjust for urls that end or dont 
            | end with a trailing slash.
            |
            '''

            if route.route_url.endswith('/'):
                matchurl = re.compile(regex.replace(r'\/\/$', r'\/$'))
            else:
                matchurl = re.compile(regex.replace(r'\/$', r'$'))

            # This will create a dictionary of parameters given. This is sort of a short
            #     but complex way to retrieve the url parameters. This is the code used to
            #     convert /url/@firstname/@lastname to {'firstmane': 'joseph', 'lastname': 'mancuso'}
            try:
                parameter_dict = {}
                for index, value in enumerate(matchurl.match(router.url).groups()):
                    parameter_dict[router.generated_url_list()[index]] = value
                request.set_params(parameter_dict)
            except AttributeError:
                pass

            '''
            |--------------------------------------------------------------------------
            | Houston, we've got a match
            |--------------------------------------------------------------------------
            |
            | Check to see if a route matches the corresponding router url. If a match
            | is found, execute that route and break out of the loop. We only need
            | one match. Routes are executed on a first come, first serve basis
            |
            '''

            if matchurl.match(router.url) and route.method_type == Environ['REQUEST_METHOD']:

                '''
                |--------------------------------------------------------------------------
                | Execute Before Middleware
                |--------------------------------------------------------------------------
                |
                | This is middleware that contains a before method.
                |
                '''

                for http_middleware in self.app.make('HttpMiddleware'):
                    located_middleware = self.app.resolve(locate(http_middleware))
                    if hasattr(located_middleware, 'before'):
                        located_middleware.before()

                # Show a helper in the terminal of which route has been visited
                print(route.method_type + ' Route: ' + router.url)

                # Loads the request in so the middleware specified is able to use the
                #     request object. This is before middleware and is ran before the request
                route.load_request(request).run_middleware('before')

                # Get the data from the route. This data is typically the output
                #     of the controller method
                if not request.redirect_url:
                    self.app.bind('Response', router.get(route.route, self.app.resolve(route.output)))

                # Loads the request in so the middleware specified is able to use the
                #     request object. This is after middleware and is ran after the request
                route.load_request(request).run_middleware('after')

                '''
                |--------------------------------------------------------------------------
                | Execute After Middleware
                |--------------------------------------------------------------------------
                |
                | This is middleware with an after method.
                |
                '''

                for http_middleware in self.app.make('HttpMiddleware'):
                    located_middleware = self.app.resolve(locate(http_middleware))
                    if hasattr(located_middleware, 'after'):
                        located_middleware.after()
                break
            else:
                data = 'Route not found. Error 404'