import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { BehaviorSubject, Observable, throwError } from 'rxjs';
import { catchError, tap } from 'rxjs/operators';
import { environment } from '../../environments/environment';

interface User {
  id: number;
  email: string;
  fname: string;
  lname: string;
  is_admin: boolean;
}

interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private apiUrl = environment.apiUrl;
  private currentUserSubject: BehaviorSubject<User | null>;
  public currentUser: Observable<User | null>;

  constructor(private http: HttpClient) {
    const storedUser = localStorage.getItem('currentUser');
    this.currentUserSubject = new BehaviorSubject<User | null>(
      storedUser ? JSON.parse(storedUser) : null
    );
    this.currentUser = this.currentUserSubject.asObservable();
  }

  public get currentUserValue(): User | null {
    return this.currentUserSubject.value;
  }

  login(email: string, password: string): Observable<AuthResponse> {
    return this.http.post<AuthResponse>(`${this.apiUrl}/auth/login`, { email, password })
      .pipe(
        tap(response => {
          // Store user details and token in local storage
          localStorage.setItem('currentUser', JSON.stringify(response.user));
          localStorage.setItem('access_token', response.access_token);
          this.currentUserSubject.next(response.user);
          return response;
        }),
        catchError(err => this.handleError(err))
      );
  }

  register(userData: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/auth/register`, userData)
      .pipe(
        catchError(err => this.handleError(err))
      );
  }

  forgotPassword(email: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/auth/forgot-password`, { email }).pipe(
      catchError(err => this.handleError(err))
    );
  }

  resetPassword(email: string, otp: string, newPassword: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/auth/reset-password`, {
      email,
      otp,
      new_password: newPassword
    }).pipe(
      catchError(err => this.handleError(err))
    );
  }

  changePassword(oldPassword: string, newPassword: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/auth/change-password`, {
      old_password: oldPassword,
      new_password: newPassword,
      confirm_new_password: newPassword
    }).pipe(
      catchError(err => this.handleError(err))
    );
  }

  logout(): void {
    // Remove user from local storage
    localStorage.removeItem('currentUser');
    localStorage.removeItem('access_token');
    this.currentUserSubject.next(null);
  }

  getToken(): string | null {
    return localStorage.getItem('access_token');
  }

  isLoggedIn(): boolean {
    return !!this.getToken();
  }

  isAdmin(): boolean {
    const user = this.currentUserValue;
    return user ? user.is_admin : false;
  }

  private handleError(error: HttpErrorResponse): Observable<never> {
    let errorMsg = '';
    if (error.error) {
      // FastAPI validation errors come back with { detail: ... }
      if (typeof error.error === 'string') {
        errorMsg = error.error;
      } else if (error.error.detail) {
        // detail can be string or list
        if (Array.isArray(error.error.detail)) {
          errorMsg = error.error.detail.map((d: any) => d.msg || JSON.stringify(d)).join(' \n');
        } else {
          errorMsg = error.error.detail;
        }
      } else {
        errorMsg = JSON.stringify(error.error);
      }
    } else {
      errorMsg = error.message;
    }
    return throwError(() => new Error(errorMsg));
  }
}
