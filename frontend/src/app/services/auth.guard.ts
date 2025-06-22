import { Injectable } from '@angular/core';
import { Router, CanActivate, ActivatedRouteSnapshot, RouterStateSnapshot } from '@angular/router';
import { AuthService } from './auth.service';

@Injectable({
  providedIn: 'root'
})
export class AuthGuard implements CanActivate {
  constructor(
    private router: Router,
    private authService: AuthService
  ) {}

  canActivate(route: ActivatedRouteSnapshot, state: RouterStateSnapshot) {
    if (this.authService.isLoggedIn()) {
      // Check if route requires admin role
      if (route.data['requiresAdmin'] && !this.authService.isAdmin()) {
        // User is not an admin, redirect to home page
        this.router.navigate(['/']);
        return false;
      }
      
      // Logged in and has required role, so return true
      return true;
    }

    // Not logged in, redirect to login page with return url
    this.router.navigate(['/login'], { queryParams: { returnUrl: state.url } });
    return false;
  }
}
